import socket
import json
import subprocess
import uuid

SOCKET_PORT = 44372
SERVER_SUPPORTED_BACKENDS = ["c", "cuda", "python", "random nonsense"]

def read_incoming(socket: socket.socket):
    buffer = b''
    while not buffer.decode("utf-8").endswith("\r\n"):
        buffer += socket.recv(1)
    return buffer
    

def send_body(socket: socket.socket, body: dict, error=""):
    socket.send((json.dumps({"body": body, "error": error}) + "\r\n").encode("utf-8"))


def parse_incoming(socket: socket.socket):
    message = json.loads(json.loads(read_incoming(s).decode('utf-8'))["body"])
    uuid = message["uuid"]
    output = None
    try:
        output = compile_and_run_code(message)
    except subprocess.TimeoutExpired:
        output = {"compile_time": "Timeout", "run_time": "Timeout"}
    
    if output is None:
        output = {"compile_time": "", "run_time": "No output was generated"}
    
    return {"uuid": uuid, "output": output}

def compile_and_run_code(json):
    timeout = json["timeout"]
    compiler_version = json["compiler-version"]
    code_backend = json["code-backend"]
    executable_options = json["executable-options"]
    code = json["code"]

    filename = uuid.uuid4().hex
    with open(f'/tmp/{filename}.fut', "w") as file:
        file.write(code)
    output = {"compile_time": "", "run_time": ""}
    result = subprocess.run(["futhark", code_backend, f'/tmp/{filename}.fut'], capture_output=True, text=True, timeout=timeout)
    output["compile_time"] = result.stderr
    if result.returncode != 0:
        return output
    result = subprocess.run([f'/tmp/{filename}'] + executable_options, capture_output=True, text=True, timeout=timeout, input="0").stdout
    output["run_time"] = result
    return output

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("127.0.0.1",SOCKET_PORT))
send_body(s, {"supported_backends": SERVER_SUPPORTED_BACKENDS})
while True:
    # Parse incoming code requests, compile and execute the code, then return the result.
    send_body(s, parse_incoming(s))