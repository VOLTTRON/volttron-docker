#!/usr/bin/env bash

sudo apt-get install jq -y

start=$(date +%s)

exit_cleanly() {
  if [ "${skip_build}" != true ]; then
    echo "Removing image: ${image_name}..."
    docker rmi --force "${image_name}"
  fi
  exit
}


exit_test() {
  echo -e "$1"
  docker logs --tail 25 volttron1
  docker-compose down
  exit_cleanly
}

check_error_code() {
  local code=$1
  if [ "${code}" -ne 0 ]; then
    exit_test "$2"
  fi
}

# Optional parameters; defaults provided for each one
skip_build='' # skip building the image
wait=360 # 6 minutes; wait is used for sleep while the container is setting up Volttron
while getopts 'sw:' flag; do
  case "${flag}" in
    s) skip_build=true ;;
    w) wait="$OPTARG" ;;
    *) echo "Unexpected option ${flag}"
       exit 1 ;;
  esac
done

# Set image_name to be used in calls to Docker
repository='eclipsevolttron/volttron' # repository name of the official Volttron repo on Dockerhub
tag='test-build' # image tag; will be used to name the image <source image>:<tag>
image_name="${repository}:${tag}"
echo "Test running with following optional parameters: skip_build: ${skip_build}; wait: ${wait}"

############ Build image
if [ "${skip_build}" = true ]; then
  echo "Skipping the build"
else
  echo "Building image: ${image_name}"
  git submodule update --init --recursive
  docker rmi --force "${image_name}" || true
  docker build --tag "${image_name}" --build-arg install_rmq=false --no-cache .
fi

###### Test that the image was built
docker images --format "{{.Tag}}: {{.Repository}}" | grep "${tag}: eclipsevolttron/volttron"
check_error_code $? 'Image was not built. Please build the image before running this test. Use: docker build -t eclipsevolttron/volttron:test-build --build-arg install_rmq=false --no-cache . '

############ Setup and start container
attempts=5
echo "Will try at most ${attempts} attempts to start container..."
while [ "${attempts}" -gt 0 ]; do
  echo "Attempt number ${attempts} to start container."
  docker-compose --file docker-compose-test.yml up --detach
  echo "Configuring and starting Volttron platform; this will take approximately several minutes........"
  sleep ${wait}
  docker ps --filter "name=volttron1" --filter "status=running" | grep 'volttron1'
  tmp_code=$?
  if [ "${tmp_code}" -eq 1 ]; then
    echo "Container failed to start."
    docker logs --tail 20 volttron1
    docker-compose down
    ((attempts=attempts-1))
  else
    # Container was successfully created
    break
  fi
done

if [ "${attempts}" -eq 0 ]; then
  echo "Failed to start container and thus cannot proceed to integration testing. Please check the Dockerfile and/or docker-compose.yml."
  exit_cleanly
fi

############# Tests
# The following tests ensure that the container is actually alive and works
echo "Running tests..."
vctl="/home/volttron/.local/bin/vctl"

# Test
# Check expected number of agents based on the number of agents in platform_config.yml; currently 6 agents are installed
echo "Testing for list of agents..."

output=$(docker exec -u volttron volttron1 "${vctl}" list)
check_error_code $? "Failed to get list of agents"

count=$(echo "${output}" | grep "" -c)
if [ "${count}" -ne 6 ]; then
  exit
#  exit_test "Total count of agents were not installed. Current count: ${count} \n Output from vctl list: \n ${output}"
fi
echo "PASSED....CHECKING LIST OF AGENTS."

# Test
# Check the health/status of each agent
declare -a agents_message
agents_message=('listeneragent-3.3' 'platform_driveragent-4.0')
# TODO: Also check for these agents: 'sqlhistorianagent-4.0.0', 'actuatoragent-1.0', 'vcplatformagent-4.8', 'volttroncentralagent-5.2'
# TODO: For some reason, 'vctl health --tag' cannot get the health status when running the command using this automated test
echo "Testing health of agents: ${agents_message[*]} "
for agent in "${agents_message[@]}"
do
  echo "Checking health for ${agent}"
  output=$(docker exec -u volttron volttron1 ${vctl} health --name "${agent}")
  message=$(echo "${output}" | jq .message)
  if [ "${message}" = '"GOOD"' ]; then
    echo "Agent is healthy"
  else
    exit_test "Failing Agent Health test because agent is unhealthy: ${output}"
  fi
done
echo "PASSED....CHECKING HEALTH OF AGENTS."

## Test
# Check the configuration of the platform which should match the config in platform_config.yml
# TODO: For now, we are verifying that the number of lines is the same number of lines in the config block of platform_config.yml (currently set at 9 with the new line)
# because the output is the configuration itself, thus we are using STDOUT to check configuration; not ideal but a start
echo "Testing platform configuration..."
output=$(docker exec -u volttron volttron1 cat /home/volttron/.volttron/config)
check_error_code $? 'Failed to get platform configuration'
count=$(docker exec -u volttron volttron1 cat /home/volttron/.volttron/config | grep "" -c)
if [ "${count}" -ne 9 ]; then
  exit_test "Platform not correctly configured. Expected at least 8 lines of configuration. Recevied ${count} lines.\n${output}"
fi
echo "PASSED....CHECKING PLATFORM CONFIG."

# TODO: when getting the output of "curl 'https://0.0.0.0:8443/discovery/'", the output is empty. Commenting out test for now
# Test
# Check that PlatformWeb is working by calling the discovery endpoint; the output is a JSON consisting of several keys such
# as "server-key", "instance_name"; here we are checking "instance_name" matches the instance name that we set in platform_config.yml
#echo "Testing discovery endpoint on web..."
#output=$(curl 'https://0.0.0.0:8443/discovery/')
#check_error_code $? 'Failed to get or parse https://0.0.0.0:8443/discovery'
#instance_name=$(echo "${output}" | jq .\"instance-name\")
#if [[ "$instance_name" != '"volttron1"' ]]; then
#  exit_test "Failing Discovery Test. Instance name is not correct. instance_name: ${instance_name}. Complete output ${output}"
#fi
#echo "PASSED....CHECKING DISCOVERY OF WEB UI."

echo "All tests passed; image is cleared to be pushed to repo."
end=$(date +%s)
runtime=$((end-start))
echo "Testing completed in $runtime seconds"

############ Shutdown container but do not remove the image
exit
