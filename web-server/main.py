from flask import Flask, render_template, request, escape, g
import hashlib
import uuid
import json
import sqlite3
from socket_server import SocketServer
import logging
import sys

app = Flask("playground-futhark")
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
    snippet = DEFAULT_SNIPPET

    if hash:
        snippet = get_snippet(hash)
    
    return render_template('index/index.html', snippet=escape(snippet))

@app.route('/run', methods=['POST'])
def run():
    return run_on_gpu(request.data.decode('utf-8'))
    

@app.route('/share', methods=['POST'])
def share():
    return insert_snippet(request.data.decode("utf-8"))

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

def run_on_gpu(code: str) -> str:
    request = json.dumps({
        "uuid": uuid.uuid4().hex, 
        "timeout": 1, 
        "compiler-version": "0.23.1", 
        "code-backend": "c",
        "executable-options": ["--log", "--debugging"],
        "code": code})
    return socket_server.execute_compute("c", request)