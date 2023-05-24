# [futhark-playground.org](http://playground.futhark-lang.org/)- a web service for interacting with futhark literate
A simple playground for running and sharing futhark snippets. The playground runs [futhark literate](https://futhark-lang.org/examples/literate-basics.html) code and outputs the corresponding markdown and images.

The playground consists of a Python flask server, and a Python socket server. The code submitted by users is not run by the flask server, but is instead run by one of the clients connected to the socket server.


## Running the project
To run the project you need to install
[Python](https://www.python.org/) and install the dependencies found
in requirements.txt (with pip: `pip install -r requirements.txt`).

You also need Futhark on the system running the compute server.

### Running the web server

```
$ cd web-server && python flask_server.py
```

Listens to HTTP connections on 127.0.0.1:5050.

When the web-server also starts a socket server at
127.0.0.1:44372. Compute servers can connect to this port.

### Running a compute client

```
$ cd compute-client && python compute-client.py
```

Connects to the socket server at 127.0.0.1:44372, and awaits requests,
which contains Futhark code, and some instructions, which it will use
to run the code. The compute_server will fail to run if there are no
servers listening on port 44372.

There is also a Dockerfile in `compute-client` as well as a script
`run-compute-client.sh` in the root of the repository that builds a
Docker image and runs the client.

### Cached files
The Futhark literate code output is saved by the web server upon successful executions.
It is saved in ```./web-server/static/literate-files```, which might be relevant if you are running the web server in docker and want the cache to persist.
