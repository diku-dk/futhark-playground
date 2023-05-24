import socket
import threading
import queue
import json
import random
import socket_util
from logger import logger as LOGGER

SOCKET_PORT = 44372
SOCKET_HOST = "127.0.0.1"
SERVER_SUPPORTED_BACKENDS = ["c", "literate", "opencl", "cuda", "python"]

def parse_incoming(socket: socket.socket):
    incoming = socket_util.read_incoming(socket).decode("utf-8")
    return json.loads(incoming)

class JobQueue():
    def __init__(self):
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.lock = threading.Lock()

class SocketClientConnection(threading.Thread):
    def __init__(self, clientsocket: socket.socket, address):
        super(SocketClientConnection, self).__init__()
        self.clientsocket = clientsocket
        self.address = address
        self.job_queue = JobQueue()
        self.alive = True
        self.supported_backends = []

    def run(self):
        self.clientsocket.settimeout(30)
        while self.alive:
            try:
                request = self.job_queue.request_queue.get()
                LOGGER.debug("Socket client connection trying to execute request")
                socket_util.send_body(self.clientsocket, request)
                self.job_queue.response_queue.put(parse_incoming(self.clientsocket))
            except Exception as error:
                LOGGER.debug("An error occurred with a client from address %s", self.address)
                LOGGER.debug(error)
                break
        self.disconnect()
    
    def disconnect(self):
        self.alive = False
        self.clientsocket.close()


class SocketServer(threading.Thread):
    def __init__(self):
        super(SocketServer, self).__init__()
        self.connected = False
        self.backend_to_clients_dict: dict[str, list[SocketClientConnection]] = {}

    def receive_supported_backends(self, clientsocket: socket.socket) -> list[str]:
        return parse_incoming(clientsocket)["body"]["supported_backends"]

    def add_client(self, client_connection: SocketClientConnection):
        supported_backends = self.receive_supported_backends(client_connection.clientsocket)
        client_connection.supported_backends = supported_backends
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
    
    def remove_client(self, client_connection: SocketClientConnection):
        for supported_backend in client_connection.supported_backends:
            if supported_backend not in self.backend_to_clients_dict:
                continue
            if client_connection not in self.backend_to_clients_dict[supported_backend]:
                continue
            self.backend_to_clients_dict[supported_backend].remove(client_connection)

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
                client_connection.run()
            except:
                continue
            LOGGER.info("Socket server started communicating with client with address %s", address)

    def execute_compute(self, backend, request):
        LOGGER.debug("Socket server sending request to a backend that supports %s", backend)
        if backend not in self.backend_to_clients_dict:
            return {"body": {}, "error": "Could not find any clients for the chosen backend."}
        while len(self.backend_to_clients_dict[backend]) > 0:
            client = random.choice(self.backend_to_clients_dict[backend])
            if not client.alive:
                self.remove_client(client)
                continue
            with client.job_queue.lock:
                if not client.alive:
                    self.remove_client(client)
                    continue
                client.job_queue.request_queue.put(request)
                try:
                    return client.job_queue.response_queue.get(block=True, timeout=10)
                # Queue.empty is returned from get if no item was available before timeout
                except queue.Empty:
                    client.disconnect()
                    self.remove_client(client)
                    continue
        
        return {"body": {}, "error": "Could not find any clients for the chosen backend."}