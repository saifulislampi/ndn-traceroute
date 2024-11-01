#!/bin/sh

# standard setup
mkdir -p build
cd build
cmake ..
make
cd ..

# build the nfd-base image
docker build -f NFD/Dockerfile -t nfd-base --target build NFD/

# build the producer image:
docker build -f producer/Dockerfile -t nfd-producer .

# run a producer:
docker run -e SOCK_NAME=test_producer -v /run/nfd:/run/nfd nfd-producer
