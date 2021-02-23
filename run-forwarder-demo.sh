#!/usr/bin/env bash

docker-compose down
git submodule update --init --recursive
docker-compose -f docker-compose-multi.yml up --build

# needed if need to build and restart the forwarder agent
#docker exec -itu volttron volttron2 /home/volttron/.local/bin/vctl shutdown
#docker exec -itu volttron volttron2 /home/volttron/.local/bin/vctl start forwarderagent-5.1

