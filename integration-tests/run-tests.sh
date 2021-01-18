#!/bin/bash
# set -x # log all shell commands for debugging.
set -e # fail if any command errors without being caught with an || or an 'if'.

start=$(date +%s.%N)

docker system prune --force

git submodule update --init --recursive

docker rmi volttron/volttron:develop --force

docker build -t volttron/volttron:develop .

#docker-compose up --detach
#
#sleep 120
## or test for connection
#
#docker exec -u volttron volttron1 /home/volttron/.local/bin/vctl status
#
##docker exec -u volttron volttron1 /home/volttron/.local/bin/vctl status
#
#docker-compose down

dur=$(echo "$(date +%s.%N) - $start" | bc)

printf "Execution time: %.6f seconds" $dur

echo "Image testing finished"