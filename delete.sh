#!/bin/bash
docker rm -f $(docker ps -a -q)
# Deleting all images
docker rmi -f $(docker images -aq)

# Deleting all containers
docker rm -f $(docker rm -aq)
