import socket
import threading
from queue import Queue
import json
import random
import logging


SOCKET_PORT = 44372
SOCKET_HOST = "127.0.0.1"
SERVER_SUPPORTED_BACKENDS = ["c", "cuda", "opencl", "python"]
LOGGER = logging.getLogger("playground-futhark.sub")


def read_incoming(socket: socket.socket):
    buffer = b''
    while not buffer.decode("utf-8").endswith("\r\n"):
        buffer += socket.recv(1)
    return buffer


def parse_incoming(socket: socket.socket):
    incoming = read_incoming(socket).decode("utf-8")
    LOGGER.debug("Incoming: %s", incoming)
    return json.loads(incoming)


def send_body(socket: socket.socket, body: dict, error=""):
    socket.send((json.dumps({"body": body, "error": error}) + "\r\n").encode("utf-8"))


class JobQueue():
    def __init__(self):
        self.request_queue = Queue()
        self.response_queue = Queue()
        self.lock = threading.Lock()


class SocketClientHandshake():
    def __init__(self, supported_backends: list[str]):
        self.supported_backends = supported_backends


class SocketClientConnection(threading.Thread):
    def __init__(self, clientsocket: socket.socket, address):
        super(SocketClientConnection, self).__init__()
        self.clientsocket = clientsocket
        self.address = address
        self.job_queue = JobQueue()
        self.alive = True

    def run(self):
        self.clientsocket.settimeout(30)
        while True:
            if self.job_queue.request_queue.empty():
                continue
            try:
                LOGGER.debug("Socket client connection trying to execute request")
                send_body(self.clientsocket, self.job_queue.request_queue.get())
                self.job_queue.response_queue.put(parse_incoming(self.clientsocket))
            except socket.error:
                break
        self.alive = False


class SocketServer(threading.Thread):
    def __init__(self):
        super(SocketServer, self).__init__()
        self.connected = False
        self.backend_to_clients_dict: dict[str, list[SocketClientConnection]] = {}

    def receive_supported_backends(self, clientsocket: socket.socket) -> list[str]:
        return parse_incoming(clientsocket)["body"]["supported_backends"]

    def add_client(self, client_connection: SocketClientConnection):
        supported_backends = self.receive_supported_backends(client_connection.clientsocket)
        LOGGER.debug("Socket server received supported backends from client: %s", supported_backends)
        if type(supported_backends) is not list or not supported_backends:
            return

        for supported_backend in supported_backends:
            if supported_backend not in SERVER_SUPPORTED_BACKENDS:
                continue

            backend_to_clients = []
            if supported_backend in self.backend_to_clients_dict:
                backend_to_clients = self.backend_to_clients_dict[supported_backend]
            backend_to_clients.append(client_connection)

            self.backend_to_clients_dict[supported_backend] = backend_to_clients

    def run(self):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind((SOCKET_HOST, SOCKET_PORT))
        serversocket.listen(5)
        LOGGER.info("Socket server running at %s:%s", SOCKET_HOST, SOCKET_PORT)
        while True:
            (clientsocket, address) = serversocket.accept()
            LOGGER.info("Socket server connected to client with address %s", address)
            clientsocket.settimeout(10)

            client_connection = SocketClientConnection(clientsocket, address)
            try:
                self.add_client(client_connection)
            except:
                continue
            client_connection.run()
            LOGGER.info("Socket server started communicating with client with address %s", address)

    def execute_compute(self, backend, request):
        LOGGER.debug("Socket server sending request (%s) to a backend that supports %s", request, backend)
        if backend not in self.backend_to_clients_dict:
            return {"body": {}, "error": "Could not find any clients for the chosen backend."}
        clients = self.backend_to_clients_dict[backend]
        while len(clients) > 0:
            client = random.choice(clients)
            if not client.alive:
                clients.remove(client)
                self.backend_to_clients_dict[backend] = clients
                continue

            with client.job_queue.lock:
                client.job_queue.request_queue.put(request)
                try:
                    return client.job_queue.response_queue.get(block=True, timeout=10)
                except:
                    continue
        
        return {"body": {}, "error": "Could not find any clients for the chosen backend."}