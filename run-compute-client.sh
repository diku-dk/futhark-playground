#!/bin/sh
#
# Build a compute client Docker image and run it.

PORT=44372
SERVER=localhost
sudo docker build -t futhark-playground-client playground-client
sudo docker run --network=host --dns=8.8.8.8 --env PORT=$PORT --env SERVER=$SERVER futhark-playground-client
