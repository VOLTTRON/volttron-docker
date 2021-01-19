#!/bin/bash
# set -x # log all shell commands for debugging.
set -e # fail if any command errors without being caught with an || or an 'if'.

# shellcheck disable=SC2006
start=$(date +%s)

docker system prune --force

git submodule update --init --recursive

docker rmi volttron/volttron:develop --force

echo "Building image..."
docker build -t volttron/volttron:develop .

echo "Testing image"

docker-compose up --detach

sleep 240
## or test for connection

# The following tests ensure that the container is actually alive and works
docker exec -u volttron volttron1 /home/volttron/.local/bin/vctl status

docker-compose down

end=$(date +%s)
runtime=$((end-start))
echo "Testing completed in $runtime seconds"

echo "Image testing finished"