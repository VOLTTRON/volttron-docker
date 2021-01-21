#!/bin/bash
# set -x # log all shell commands for debugging.
set -e # fail if any command errors without being caught with an || or an 'if'.
# install jq for testing
sudo apt-get install jq -y
start=$(date +%s)


exit_cleanly() {
  docker-compose down
  if [ "$skip_build" != true ]; then
    echo "Removing image..."
    docker rmi ${image_name}
  fi
}


exit_test() {
  echo "Failed test. Exiting..."
  exit_cleanly
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

# Set image_name to be used in calls to docker
image_name="${group}/volttron:${tag}"

echo "Test running with following optional parameters: $skip_build $wait $group $tag"

############ Build image
if [ "$skip_build" = true ]; then
  echo "Skipping the build"
else
  echo "Building image..."
  git submodule update --init --recursive
  docker rmi "${image_name}" --force
  docker build --no-cache -t "${image_name}" .
fi


docker images

############ Setup and start container
attempts=5
while [ ${attempts} -gt 0 ]; do
  echo "Attempt to start container: ${attempts}"
  docker-compose up --detach
  sleep 2
  has_volttron1=$(docker ps --filter "name=volttron1" | grep "" -c)
  if [ ${has_volttron1} -eq 1 ]; then
    echo "Container failed to start."
    docker logs -n 20 volttron1
    docker-compose down
    ((attempts=attempts-1))
  else
    # Container was successfully created
    echo "Configuring and starting Volttron platform; this will take approximately several minutes........"
    break
  fi
done

############# Tests
# The following tests ensure that the container is actually alive and works
sleep "$wait"
echo "Running tests..."
set +e

# Test 1
# Check expected number of agents based on the number of agents in platform_config.yml
vctl="/home/volttron/.local/bin/vctl"
count=$(docker exec -u volttron volttron1 /home/volttron/.local/bin/vctl list | grep "" -c)
docker logs -n 20 volttron1
check_test_execution $? "Failed to get list of agents"
if [ $count -ne 6 ]; then
  echo "Total count of agents were not installed. Current count: $count"
  docker exec -u volttron volttron1 /home/volttron/.local/bin/vctl list
  exit_test
fi

## Test 2
# Check the configuration of the platform which should match the config in platform_config.yml
# For now, we are verifying that the number of lines is the same number of lines in the config block of platform_config.yml (currently set at 8 with the new line)
# because the output is the configuration itself, thus we are using STDOUT to check configuration; not ideal but a start
count=$(docker exec -u volttron volttron1 cat /home/volttron/.volttron/config | grep "" -c)
check_test_execution $? 'Failed to get platform configuration'
if [ $count -ne 8 ]; then
  echo "Platform not correctly configured. Expected at least 6 lines of configuration."
  docker exec -u volttron volttron1 cat /home/volttron/.volttron/config
  exit_test
fi

# Test 3
# Check that PlatformWeb is working by calling the discovery endpoint; the output is a JSON consisting of several keys such
# as "server-key", "instance_name"; here we are checking "instance_name" matches the instance name that we set in platform_config.yml
instance_name=$(curl -s http://0.0.0.0:8080/discovery/ | jq .\"instance-name\")
check_test_execution $? 'Failed to get or parse http://0.0.0.0:8080/discovery'
if [[ "$instance_name" != '"volttron1"' ]]; then
  echo "Instance name is not correct. instance_name: $instance_name"
  exit_test
fi

set -e
echo "All tests passed; image is cleared to be pushed to repo."
end=$(date +%s)
runtime=$((end-start))

############ Shutdown container/cleanup
exit_cleanly
echo "Testing completed in $runtime seconds"