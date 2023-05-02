from flask import Flask, render_template, request, escape
from flask_cors import CORS
import hashlib
import json
from socket_server import SocketServer
import base64
import os
import re
from waitress import serve
import argparse
from logger import logger as LOGGER

parser = argparse.ArgumentParser(description='Run the futhark playground web server server')
parser.add_argument('--port', metavar='port', type=int,
                    help='the port of the web server', default=5000)
parser.add_argument('--address', metavar='address', type=str,
                    help='the address of the web server', default='127.0.0.1')
args = parser.parse_args()

WEBSERVER_PORT = args.port
WEBSERVER_ADDRESS = args.address

app = Flask("playground-futhark", static_url_path='/static')
cors = CORS(app, resources={r"*": {"origins": "*"}})

default_snippet_file = open("./static/default-snippets/literate-basics.fut", "r")
DEFAULT_SNIPPET = default_snippet_file.read()
default_snippet_file.close()

##################################
########## FLASK THINGS ##########
##################################

@app.route('/', defaults={'hash': None})
@app.route('/<hash>')
def index(hash):
    backend = request.args.get("backend", default="c")
    version = request.args.get("version", default="latest")
    snippet = None
    snippet_output = None
    compile_time_output = None

    if hash:
        snippet = get_snippet(hash)
        snippet_output = get_snippet_output(hash)
        compile_time_output = get_compile_time_output(hash)
    
    if not snippet_output:
        snippet_output = ""

    if not compile_time_output:
        compile_time_output = ""
    
    if not snippet:
        snippet = DEFAULT_SNIPPET

    return render_template('index/index.html', 
        snippet=escape(snippet), 
        backend=escape(backend), 
        version=escape(version),
        literate_content=snippet_output,
        compile_time_output=compile_time_output)

@app.route('/run', methods=['POST'])
def run():
    backend = request.args.get("backend", default="c")
    version = request.args.get("version", default="latest")

    return run_literate(request.data, backend, version)


@app.route('/share', methods=['POST'])
def share():
    return insert_snippet(request.data.decode("utf-8"))

#####################################
########## FILE MANAGEMENT ##########
#####################################


def get_snippet(hash: str):
    if not os.path.exists(f"./static/literate-files/{hash}.fut"):
        return None
    with open(f"./static/literate-files/{hash}.fut", "r") as file:
        return file.read()

def insert_snippet(snippet: str):
    hash = hashlib.sha256(snippet.encode()).hexdigest()
    with open(f"./static/literate-files/{hash}.fut", "w") as file:
        file.write(snippet)
    return hash

def get_snippet_output(hash):
    if not os.path.exists(f"./static/literate-files/{hash}/{hash}.md"):
        return None
    with open(f"./static/literate-files/{hash}/{hash}.md", "r") as file:
        return file.read()

def get_compile_time_output(hash):
    if not os.path.exists(f"./static/literate-files/{hash}/compile_time.txt"):
        return None
    with open(f"./static/literate-files/{hash}/compile_time.txt", "r") as file:
        return file.read()


#####################################
########## LITERATE THINGS ##########
#####################################

def run_literate(data: bytes, backend:str, version: str):
    hash = hashlib.sha256(data).hexdigest()
    compute_output = {"body": {"output": {"compile_time": "", "literate": ""}}, "error": ""}

    if not os.path.exists(f"./static/literate-files/{hash}.md"):
        try:
            compute_output = run_on_compute_server(request.data.decode('utf-8'), backend, version)
            if compute_output["error"]:
                return compute_output
        except:
            compute_output["error"] = "An error occurred while processing processing your request."
        if compute_output["body"]["output"]["compile_time"]:
            compute_output["body"]["output"]["compile_time"] = re.sub(r"/tmp/[a-f0-9]*\.fut", "program.fut", compute_output["body"]["output"]["compile_time"])
        try:
            if compute_output["body"]["output"]["markdown"]:
                insert_snippet(data.decode('utf-8'))
                save_literate_files(hash, compute_output)
        except:
            compute_output["error"] = "An error occurred while saving the output from your request."
    
    compute_output["body"]["output"]["literate"] = "static/empty_markdown.md"
    if os.path.exists(f"./static/literate-files/{hash}/{hash}.md"):
        compute_output["body"]["output"]["literate"] = f"static/literate-files/{hash}/{hash}.md"
    if os.path.exists(f"./static/literate-files/{hash}/compile_time.txt"):
        with open(f"./static/literate-files/{hash}/compile_time.txt", "r") as file:
            compute_output["body"]["output"]["compile_time"] = file.read()

    return compute_output

def save_literate_files(hash, compute_server_data:dict):
    output = compute_server_data["body"]["output"]
    if not os.path.exists(f"./static/literate-files/{hash}"):
        os.makedirs(f"./static/literate-files/{hash}")

    compile_time = output["compile_time"]
    if compile_time:
        with open(f"./static/literate-files/{hash}/compile_time.txt", "w") as file:
            file.write(compile_time)

    images_base64 = output["images"]
    for image in images_base64:
        path = image[0]
        file_bytes = base64.b64decode(image[1].encode("ascii"))
        with open(f"./static/literate-files/{path}", "wb") as file:
            file.write(file_bytes)

    markdown_file:str = output["markdown"]
    if markdown_file:
        markdown_file = markdown_file.replace(f"{hash}-img", f"static/literate-files/{hash}")
        with open(f"./static/literate-files/{hash}/{hash}.md", "w") as file:
            file.write(markdown_file)

if not os.path.exists(f"./static/literate-files"):
    os.makedirs(f"./static/literate-files")

#####################################
########### SOCKET THINGS ###########
#####################################

socket_server = SocketServer()
socket_server.start()

def run_on_compute_server(code: str, backend: str, version: str) -> str:
    request = json.dumps({
        "uuid": hashlib.sha256(code.encode()).hexdigest(), 
        "timeout": 5.0, 
        "compiler-version": version, 
        "code-backend": backend,
        "executable-options": ["--log", "--debugging"],
        "code": code})
    return socket_server.execute_compute(backend, request)


if __name__ == "__main__":
    LOGGER.info(f"Starting webserver at {WEBSERVER_ADDRESS}:{WEBSERVER_PORT}")
    serve(app, host=WEBSERVER_ADDRESS, port=WEBSERVER_PORT)