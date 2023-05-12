# futhark-playground - a web service for interacting with futhark
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

Listens to HTTP connections on 127.0.0.1:5000.

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

## Communication between web-server and compute-server
The communication between the server and clients is a simple TCP connection. The server can have an unlimited amount of clients connected to it, and it will at random choose which client to send run requests to.

All exchanges starts with 1 byte, indicating the size of the incoming data. If the first bit is set to 1, then the remaining 7 bits is used to determine how many bytes are needed to specify the length of the data. The data itself is in JSON. 

When a client connects to the server, it has to communicate which code backends it supports. The "hello" from the client looks like this:
```
{
    "body": 
        {
            "supported_backends": ['c', 'opencl', 'whatever backend you support']
        }
    "error": ""
}
```
The server will then keep the supported_backends in mind when assigning which client should run which snippet.
The requests from the server to the client will have the same format as below, but values may vary:
```
{
    "body": 
        {
            "uuid": "random uuid",
            "timeout": "1",
            "compiler-version": "0.23.1",
            "code-backend": "c",
            "executable-options": ["--help", "--log", "--debugging"],
            "code": "very cool code"
        }
    "error": ""
}
```
The respond from the client should follow the following format:
```
{
    "body": 
        {
            "uuid": "the same uuid as the request from the server",
            "output":
                {
                    "compile_time": "compile output"
                    "markdown": "markdown"
                    "images:" [] 
                }
        }
    "error": "any potential errors that has occurred"
}
```
