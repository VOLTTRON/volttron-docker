# Official VOLTTRON docker image

# Introduction

This image provides a reproducible way to install VOLTTRON within a docker container.
By using a volume mount of the `VOLTTRON_HOME` directory, runtime changes made by the platform are visible on the host and are preserved across instances of the container.
Similarly, changes made from the host are reflected in the container.
The image uses the utility [gosu](https://github.com/tianon/gosu), which allows the non-root user executing the volttron platform inside the container to have the same UID as the host user running the container on the host system.
In conjunction with volume mounting of the directory, this ensures that file ownership and permissions in `VOLTTRON_HOME` match the host user, avoiding cases where root in the container leaves files inaccessible to a user without sudo permissions on the host.

# Prerequisites

* Docker
* Docker-compose

If you need to install docker and/or docker-compose, you can use the script in this repo. From the root level, execute the following command:

```bash
$ ./docker_install_ubuntu.sh
```


# Quickstart using Docker-Compose

To create the container and start using the platform on the container, run the following command from the command line. Ensure that you are in the root level of the directory.
Note that there are two docker-compose files:
* docker-compose.yml: creates a single Volttron instance with ZMQ message bus
* docker-compose.yml: creates a single Volttron instance with RMQ message bus

``` bash
# Creates Volttron instance with ZMQ message bus
$ docker-compose up

# To create a Volttron instance with RMQ message bus
$ docker-compose -f docker-compose-rmq.yml up 

# To look inside the container
$ docker-compose exec volttron bash 

# To stop the container
$ docker-compose stop 

# To start the container after it's been stopped
$ docker-compose start 

# To get a list of all containers created from docker-compose
$ docker-compose ps
```

For Volttron instance using ZMQ message bus:
* Set the master username and password on the Volttron Central Admin page at `http://0.0.0.0:8080/index.html` 
* To log in to Volttron Central, open a browser and login to the Volttron web interface: `http://0.0.0.0:8080/vc/index.html`

For Volttron instances using RMQ message bus:
* Set the master username and password on the Volttron Central Admin page at `https://0.0.0.0:8443/index.html` 
* To log in to Volttron Central, open a browser and login to the Volttron web interface: `https://0.0.0.0:8443/vc/index.html`


# Platform Initialization

The VOLTTRON container when created is just a blank container with no agents.  Now there is an initialization routine available within the docker container to allow the installation of agents before launching of the instance.  To do this one will mount a `platform_config.yml` file to `/platform_config.yml` within the container. One is also likely to need to mount agent configurations (specified in the `platform_config.yml` file), into the container. The recommended way to do this is through a `docker-compose.yml` file.  An example of this is included in this repository, based on the one in the [volttron-fuel-cells repo](https://github.com/VOLTTRON/volttron-fuel-cells/).

The `platform_config.yml` file has two sections: `config`, which configures the main instance and populate's the main config file ($VOLTTRON_HOME/config), and `agents`, which contains a list of agents with references to configurations for them (note the frequent use of environment variables in this section).

## Main Configuration
The main instance configuration is composed of key value pairs under a "config" key in the `platform_config.yml` file.
For example, the `vip-address` and `bind-web-address` would be populated using the following partial file:
``` yaml
# Properties to be added to the root config file:
# - the properties should be ingestable for volttron
# - the values will be presented in the config file
#   as key=value
config:
  vip-address: tcp://0.0.0.0:22916
  bind-web-address: http://0.0.0.0:8080
  # volttron-central-address: a different address
  # volttron-central-serverkey: a different key 

  ...
```

## Agent Configuration
The agent configuration section is under a top-level key called "agents". This top-level key contains several layers of nested key-value mappings.
The top level of the section is keyed with the names of the desired agents, which are used as the identity of those agents within the platform.
For each agent key, there is a further mapping which must contain a `source` key and may contain either or both a `config` and/or `config_store` key; the values are strings representing resolvable paths.
An example follows at the end of this section.

Note that the agent section does not contain the detailed configuration of the agents; for each agent it gives a path to a dedicated configuration file for that agent.
As with the `platform_config.yaml` file, it is generally desirable to mount a local directory containing the configurations into the container, again using a `docker-compose.yaml` file.

```yaml
...

# Agents dictionary to install.  The key must be a valid
# identity for the agent to be installed correctly.
agents:

  # Each agent identity.config file should be in the configs
  # directory and will be used to install the agent.
  listener:
    source: $VOLTTRON_ROOT/examples/ListenerAgent
    config: $CONFIG/listener.config

  platform.actuator:
    source: $VOLTTRON_ROOT/services/core/ActuatorAgent

  historian:
    source: $VOLTTRON_ROOT/services/core/SQLHistorian
    config: $CONFIG/historian.config

  weather:
    source: $VOLTTRON_ROOT/examples/DataPublisher
    config: $CONFIG/weather.config

  price:
    source: $VOLTTRON_ROOT/examples/DataPublisher
    config: $CONFIG/price.config

  platform.driver:
    source: $VOLTTRON_ROOT/services/core/MasterDriverAgent
    config_store:
      fake.csv:
        file: $VOLTTRON_ROOT/examples/configurations/drivers/fake.csv
        type: --csv
      devices/fake-campus/fake-building/fake-device:
        file: $VOLTTRON_ROOT/examples/configurations/drivers/fake.config
```

## Other Notes
Agents within the `platform_config.yml` file are created sequentially, it can take several seconds for each to spin up and be visible via `vctl` commands.

# Building Image Locally

## Prerequisite

This repo has a directory called 'volttron', which contains the volttron codebase. In other words, this repo contains another repo in a subfolder. 
When you initially clone this repo, the 'volttron' directory is empty. This directory contains the volttron codebase used to create the volttron platform. 
Before creating the container, you must pull in volttron from the [official volttron repo](https://github.com/VOLTTRON/volttron) using the following git command:

```bash
# Clones https://github.com/VOLTTRON/volttron.git into the 'volttron' directory
$ git submodule update --init --recursive
```

OPTIONAL: This repo uses a specific version of volttron based on the commit in the 'volttron' submodule. If you want to use the latest volttron from the `develop` 
branch from the volttron repo, execute the following command (NOTE: this is not required):

```bash 
# Ensure that you are in the `volttron` folder
$ git pull origin develop
```

## How to build locally

To build and test this image locally, follow the steps below:

Step 1. Build the image:

```
$ docker build -t volttron_local .
```

Step 2. Run the container:

```
# Creates a docker container named "volttron1"; this container will be automatically removed when the container stops running
$ docker run \
--name volttron1 \
--rm \
-e LOCAL_USER_ID=$UID \
-e CONFIG=/home/volttron/configs \
-v "$(pwd)"/configs:/home/volttron/configs \
-v "$(pwd)"/platform_config.yml:/platform_config.yml \
-p 8080:8080 \
-it volttron_local
``` 

Step 3. Once the container is started and running, set the master username and password on the Volttron Central Admin page at `http://0.0.0.0:8080/index.html`

Step 4. To log in to Volttron Central, open a browser and login to the Volttron web interface: `http://0.0.0.0:8080/vc/index.html`

# Raw Container Usage

``` bash
# Retrieves and creates a volttron container from the volttron/volttron:develop image on Volttron DockerHub
$ docker run -it  -e LOCAL_USER_ID=$UID --name volttron1 --rm -d volttron/volttron:develop
```

After entering the above command the shell will be within the volttron container as a user named volttron.

``` bash
$ docker exec -itu volttron volttron1 bash

# check status of volttron platform
$ vctl status

# set environment variable, IGNORE_ENV_CHECK, to ignore virtual env in python
$ export IGNORE_ENV_CHECK=1

# Install a ListenterAgent
$ python3 scripts/install-agent.py -s examples/ListenerAgent --start

# check status of volttron platform to verify ListenerAgent is installed
$ vctl status

# To Stop the container
$ docker stop volttron1
```

All the same functionality that one would have from a VOLTTRON command line is available through the container.

# Advanced Usage

In order for volttron to keep its state between runs, the state must be stored on the host.  We have attempted to make this as painless as possible, by using gosu to map the hosts UID onto the containers volttron user.  The following will create a directory to be written to during VOLTTRON execution.

1. Create a directory (eg `mkdir -p ~/vhome`).  This is where the VOLTTRON_HOME inside the container will be created on the host.
1. Start the docker container with a volume mount point and pass a LOCAL_USER_ID environtmental variable.
    ``` bash
    docker run -e LOCAL_USER_ID=$UID -v /home/user/vhome:/home/volttron/.volttron -it volttron/volttron
    ```

In order to allow an external instance connect to the running volttron container one must add the -p <hostport>:<containerport> (e.g. 22916:22916)


# Development

## Dockerfile 

If you want to work on improving/developing the Dockerfile, you can locally run a test script to check whether the image
works as expected. To run the test, see the following:

```bash
# run the test (rebuilds and tests the most current image)
$ ./run-test-docker-image.sh

# You can also run the test but skip rebuilding the image 
$ ./run-test-docker-image.sh -s
```