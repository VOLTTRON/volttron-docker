#!/usr/bin/env bash

## these are redundant with main.sh
#echo '{"experimental":true}' | sudo tee -a /etc/docker/daemon.json
#sudo service docker restart

sudo docker run --rm --privileged multiarch/qemu-user-static:register --reset
