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


############ Parse optional parameters

# "$#" number of args passed
# "$@" list of strings of positional arguments passed

# "$*" single string of args
## ^^^ this will hand over exactly one argument, containing all
##     original arguments, separated by single spaces.

# $*
## ^^^ this will join all arguments by single spaces as well and
##     will then split the string as the shell does on the command
##     line, thus it will split an argument containing spaces into
##     several arguments.

# Optional parameters; defaults provided for each one
skip_build='' # skip building the image
wait=300 # 5 minutes; wait is used for sleep while the container is setting up Volttron
group='volttron' # group name of the image; will be used to name the image <group>/volttron
tag='develop' # image tag; will be used to name the image <source image>:<tag>
while getopts 'sw:g:t:' flag; do
  case "$flag" in
    s) skip_build=true ;;
    w) wait="$OPTARG" ;;
    g) group="$OPTARG" ;;
    t) tag="$OPTARG" ;;
    *) echo "Unexpected option ${flag}"
       exit 1 ;;
  esac
done

echo "Test running with following optional parameters: $skip_build $wait $group $tag"

############ Build image
if [ "$skip_build" = true ]; then
  echo "Skipping the build"
else
  echo "Building image..."
  git submodule update --init --recursive
  image_name="${group}/volttron:${tag}"
  docker rmi "${image_name}" --force
  docker build --no-cache -t "${image_name}" .
fi


############ Setup and start container
docker-compose up --detach
echo "Configuring and starting Volttron platform; this will take approximately several minutes........"
# need to wait until setup is complete, usually takes about 4 minutes == 240 seconds
sleep "$wait" # 4 minutes by default

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
if [ "$skip_build" != true ]; then
  echo "Removing image..."
  docker rmi volttron/volttron:develop
fi
end=$(date +%s)
runtime=$((end-start))
echo "Testing completed in $runtime seconds"