from flask import Flask, render_template, request, escape, g
import hashlib
import json
import sqlite3
from socket_server import SocketServer
import logging
import sys
import base64
import os

app = Flask("playground-futhark", static_url_path='/static')

DATABASE = "db/play-futhark.db"
DEFAULT_SNIPPET = """def mean [n] (vs: [n]f64) =
    f64.sum vs / f64.i64 n

def main (n: f64): f64 = mean [1.0,2.0,3.0,4.0]"""

### Logging
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

##################################
########## FLASK THINGS ##########
##################################

@app.route('/', defaults={'hash': None})
@app.route('/<hash>')
def index(hash):
    backend = request.args.get("backend", default="c")
    version = request.args.get("version", default="latest")
    snippet = None

    if hash:
        snippet = get_snippet(hash)
    
    if not snippet:
        snippet = DEFAULT_SNIPPET
    
    return render_template('index/index.html', 
        snippet=escape(snippet), 
        backend=escape(backend), 
        version=escape(version))

@app.route('/run', methods=['POST'])
def run():
    backend = request.args.get("backend", default="c")
    version = request.args.get("version", default="latest")

    if backend == "literate":
        return run_literate(request.data, version)

    output = run_on_compute_server(request.data.decode('utf-8'), backend, version)
    output["body"]["output"]["compile_time"] = output["body"]["output"]["compile_time"].replace(f"/tmp/{output['body']['uuid']}.fut", "program.fut")
    return output


@app.route('/share', methods=['POST'])
def share():
    return insert_snippet(request.data.decode("utf-8"))

def run_literate(data: bytes, version: str):
    hash = hashlib.sha256(data).hexdigest()

    if not os.path.exists(f"./static/literate-files/{hash}.md"):
        compute_output = run_on_compute_server(request.data.decode('utf-8'), 'literate', version)
        save_literate_files(hash, compute_output)
    
    return {"body": {"output": {"compile_time": "", "run_time": "", "literate": f"static/literate-files/{hash}.md"}}, "error": ""}

def save_literate_files(hash, compute_server_data:dict):
    output = compute_server_data["body"]["output"]
    markdown_file:str = output["markdown"]
    images_base64 = output["images"]
    for image in images_base64:
        path = image[0]
        file_bytes = base64.b64decode(image[1].encode("ascii"))
        if not os.path.exists(f"./static/literate-files/{hash}-img"):
            os.makedirs(f"./static/literate-files/{hash}-img")
        with open(f"./static/literate-files/{path}", "wb") as file:
            file.write(file_bytes)

    markdown_file = markdown_file.replace(f"{hash}-img", f"static/literate-files/{hash}-img")
    with open(f"./static/literate-files/{hash}.md", "w") as file:
        file.write(markdown_file)

if not os.path.exists(f"./static/literate-files"):
    os.makedirs(f"./static/literate-files")

#####################################
########## DATABASE THINGS ##########
#####################################

def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('db/schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
init_db()

def get_snippet(hash: str):
    snippet = get_db().cursor().execute("SELECT snippet FROM snippets WHERE hash = ?", (hash,)).fetchone()
    if snippet is not None:
        return snippet[0]
    return snippet

def insert_snippet(snippet: str):
    hash = hashlib.sha256(snippet.encode()).hexdigest()
    db = get_db()
    db.cursor().execute("INSERT OR IGNORE INTO snippets VALUES (?, ?)", (hash, snippet))
    db.commit()
    return hash


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