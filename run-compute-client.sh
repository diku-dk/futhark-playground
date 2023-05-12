#!/bin/sh
#
# Build a compute client Docker image and run it.

PORT=44372
SERVER=localhost
sudo docker build -t futhark-playground-client compute-client
sudo docker run --env PORT=$PORT --env SERVER=$SERVER futhark-playground-client
