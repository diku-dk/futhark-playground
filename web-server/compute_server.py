import socket
import json
import subprocess
import uuid
import os
import socket_util
import base64

SOCKET_PORT = 44372
SERVER_SUPPORTED_BACKENDS = ["c", "cuda", "python", "random nonsense", "literate"]

def parse_incoming(socket: socket.socket):
    message = json.loads(json.loads(socket_util.read_incoming(s).decode('utf-8'))["body"])
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

    filename = json["uuid"]
    with open(f'/tmp/{filename}.fut', "w") as file:
        file.write(code)
    output = {"compile_time": "", "run_time": ""}
    result = subprocess.run(["futhark", code_backend, f'/tmp/{filename}.fut'], capture_output=True, text=True, timeout=timeout)
    output["compile_time"] = result.stderr
    if result.returncode != 0:
        return output
    
    if code_backend == "literate":
        markdown_file = open(f"/tmp/{filename}.md", "r")
        output["markdown"] = markdown_file.read()
        output["images"] = get_literate_files(filename)
        markdown_file.close()
        return output
    
    result = subprocess.run([f'/tmp/{filename}'] + executable_options, capture_output=True, text=True, timeout=timeout, input="0").stdout
    output["run_time"] = result
    try:
        os.remove(f'/tmp/{filename}.fut')
        os.remove(f'/tmp/{filename}')
    except:
        pass
    return output

def get_literate_files(filename):
    image_directory = f"/tmp/{filename}-img"
    files = []
    for path in os.listdir(image_directory):
        file_path = os.path.join(image_directory, path)
        if not os.path.isfile(file_path):
            continue
        file = open(file_path, "rb")
        files.append([f"{filename}-img/{path}", base64.b64encode(file.read()).decode("ascii")])
        file.close()
    return files


s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("127.0.0.1",SOCKET_PORT))
socket_util.send_body(s, {"supported_backends": SERVER_SUPPORTED_BACKENDS})
while True:
    # Parse incoming code requests, compile and execute the code, then return the result.
    socket_util.send_body(s, parse_incoming(s))