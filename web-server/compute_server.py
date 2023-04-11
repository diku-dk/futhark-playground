import socket
import json
import subprocess
import os
import socket_util
import base64
import argparse


parser = argparse.ArgumentParser(description='Run the futhark playground compute server')
parser.add_argument('--port', metavar='port', type=int,
                    help='the port of the target web server', default=44372)
parser.add_argument('--address', metavar='address', type=str,
                    help='the address of the target web server', default='127.0.0.1')
args = parser.parse_args()

TARGET_SOCKET_PORT = args.port
TARGET_SOCKET_ADDRESS = args.address

SERVER_SUPPORTED_BACKENDS = ["c", "cuda", "python", "random nonsense", "literate"]

def parse_incoming(socket: socket.socket):
    message = json.loads(json.loads(socket_util.read_incoming(s).decode('utf-8'))["body"])
    uuid = message["uuid"]
    output = None
    try:
        output = compile_and_run_code(message)
    except subprocess.TimeoutExpired:
        output = {"compile_time": "Timeout"}
    
    if output is None:
        output = {"compile_time": ""}
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
    output = {"compile_time": "", "markdown": "", "images": []}
    result = subprocess.run(['futhark', 'literate', f'--backend={code_backend}', f'/tmp/{filename}.fut'], capture_output=True, text=True, timeout=timeout)
    output["compile_time"] = result.stderr
    if result.returncode != 0:
        return output
    
    markdown_file = open(f"/tmp/{filename}.md", "r")
    output["markdown"] = markdown_file.read()
    output["images"] = get_literate_files(filename)
    markdown_file.close()

    try:
        os.remove(f'/tmp/{filename}.fut')
        os.remove(f'/tmp/{filename}')
    except:
        pass
    return output

def get_literate_files(filename):
    image_directory = f"/tmp/{filename}-img"
    if not os.path.exists(image_directory):
        return []
    files = []
    for path in os.listdir(image_directory):
        file_path = os.path.join(image_directory, path)
        if not os.path.isfile(file_path):
            continue
        file = open(file_path, "rb")
        files.append([f"{filename}/{path}", base64.b64encode(file.read()).decode("ascii")])
        file.close()
    return files


s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((TARGET_SOCKET_ADDRESS,TARGET_SOCKET_PORT))
socket_util.send_body(s, {"supported_backends": SERVER_SUPPORTED_BACKENDS})
while True:
    # Parse incoming code requests, compile and execute the code, then return the result.
    socket_util.send_body(s, parse_incoming(s))