#!/bin/bash
# set -x # log all shell commands for debugging.
set -e # fail if any command errors without being caught with an || or an 'if'.

docker system prune --force

git submodule update --init --recursive

docker-compose up --build --detach

# sleep to let container build

# while statement to test con

no_
while no_connect:

docker exec -u volttron volttron1 /home/volttron/.local/bin/vctl status

# close docker


echo "Image testing finished"