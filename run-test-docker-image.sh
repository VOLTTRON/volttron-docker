#!/bin/bash
# set -x # log all shell commands for debugging.
set -e # fail if any command errors without being caught with an || or an 'if'.
# install jq for testing
sudo apt-get install jq -y
start=$(date +%s)


exit_test(){
  echo "Failed test. Exiting..."
  docker-compose down
  exit 1
}


check_test_execution() {
  local code="$1"
  if [ "$code" -ne 0 ]; then
    echo "$2"
    exit_test
  fi
}


############ Setup docker and git environments
docker system prune --force
git submodule update --init --recursive


############ Parse optional parameters
# One option to the test script is '-s' which gives the option to skip building the image
skip_build=''
while getopts 's' flag; do
  case "$flag" in
    s) skip_build=true ;;
    *) echo "Unexpected option ${flag}"
       exit 1 ;;
  esac
done


############ Build image
if [ "$skip_build" = true ]; then
  echo "Skipping the build"
else
  echo "Building image..."
  docker rmi volttron/volttron:develop --force
  docker build -t volttron/volttron:develop .
fi


############ Setup and start container
docker-compose up --detach
echo "Configuring and starting Volttron platform (this will take some time around 5 minutes)........"
# need to wait until setup is complete, usually takes about 4 minutes == 240 seconds
sleep 240

############# Tests
# The following tests ensure that the container is actually alive and works
echo "Running tests..."
set +e

# Test 1
# Check expected number of agents
count=$(docker exec -u volttron volttron1 /home/volttron/.local/bin/vctl list | grep "" -c)
check_test_execution $? "Failed to get list of agents"
if [ $count -ne 6 ]; then
  echo "Total count of agents were not installed. Current count: $count"
  docker exec -u volttron volttron1 /home/volttron/.local/bin/vctl list
  exit_test
fi

## Test 2
# Check the configuration of the platform
count=$(docker exec -u volttron volttron1 cat /home/volttron/.volttron/config | grep "" -c)
check_test_execution $? 'Failed to get platform configuration'
if [ $count -ne 8 ]; then
  echo "Platform not correctly configured. Expected at least 6 lines of configuration."
  docker exec -u volttron volttron1 cat /home/volttron/.volttron/config
  exit_test
fi

# Test 3
instance_name=$(curl -s http://0.0.0.0:8080/discovery/ | jq .\"instance-name\")
check_test_execution $? 'Failed to get or parse http://0.0.0.0:8080/discovery'
if [[ "$instance_name" != '"volttron1"' ]]; then
  echo "Instance name is not correct. instance_name: $instance_name"
  exit_test
fi

set -e
echo "All tests passed; image is cleared to be pushed to repo."

############ Shutdown container/cleanup
docker-compose down
end=$(date +%s)
runtime=$((end-start))
echo "Testing completed in $runtime seconds"