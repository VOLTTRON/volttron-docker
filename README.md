# Official VOLTTRON docker image

# Introduction

This image provides a reproducible way to install VOLTTRON within a docker container.
By using a volume mount of the `VOLTTRON_HOME` directory, runtime changes made by the platform are visible on the host and are preserved across instances of the container.
Similarly, changes made from the host are reflected in the container.
The image uses the utility [gosu](https://github.com/tianon/gosu), which allows the non-root user executing the volttron platform inside the container to have the same UID as the host user running the container on the host system.
In conjunction with volume mounting of the directory, this ensures that file ownership and permissions in `VOLTTRON_HOME` match the host user, avoiding cases where root in the container leaves files inaccessible to a user without sudo permissions on the host.

# Prerequisites

* Docker ^20.10.8
* Docker-compose ^1.29.2

If you need to install docker and/or docker-compose AND you are running this image on an Ubuntu machine, you can use the script in this repo. From the root level, execute the following command:

```bash
$ ./docker_install_ubuntu.sh
```

# Quickstart:

To create the container and start using the platform on the container, run the following commands from the command line. Ensure that you are in the root level of the directory.

```

# Build the image locally. Set <tag> to some tag. Then update the
docker-compose script with the updated image name that uses the tag as part of
its name.

# Example below
$ docker build -t eclipsevolttron/volttron:<some tag> --build-arg install_rmq=false --no-cache  .

# Create and start the container that has runs Volttron
$ docker-compose up

# SSH into the container as the user 'volttron'
$ docker exec -itu volttron volttron1 bash

# Stop the container
$ docker-compose stop

# Start the container
$ docker-compose start

# To get a list of all containers created from docker-compose
$ docker-compose ps

# To stop and remove the container
$ docker-compose down
```

For Volttron instances using ZMQ message bus:
* Set the master username and password on the Volttron Central Admin page at `https://0.0.0.0:8443/index.html`
* To log in to Volttron Central, open a browser and login to the Volttron web interface: `https://0.0.0.0:8443/vc/index.html`


# Platform Initialization

An initialization routine is available within the docker container
to allow installation of agents before launching Volttron.
To do this, mount a `platform_config.yml` file to `/platform_config.yml` within the container.
The recommended way to do this is through a `docker-compose.yml` file.  An example is included at the root level
of this repository.

The `platform_config.yml` file has two sections: `config`, which configures the main instance and populate's the main config file ($VOLTTRON_HOME/config), and `agents`, which contains a list of agents with references to configurations for them (note the frequent use of environment variables in this section).

## Main Configuration
The Volttron configuration is defined under the section "config" in `platform_config.yml`. Note: This image requires that the Volttron Platform enable web. Thus, the platform configuration must set 'bind-web-address'.

For example, the `vip-address` and `bind-web-address` would be set to specific values as seen in the following:

``` yaml
# Properties to be added to the root config file:
# - the properties should be ingestable for volttron
# - the values will be presented in the config file
#   as key=value
config:
  vip-address: tcp://0.0.0.0:22916
  bind-web-address: https://0.0.0.0:8443
  # volttron-central-address: a different address
  # volttron-central-serverkey: a different key

  ...
```

## Agent Configuration
The agent configuration section is under a top-level section named "agents". All agents that need to be defined and configured
within the Volttron platform must be listed in this section.

Each agent must have a "source", which is the path to the source code of that agent.
An agent can also have an optional `config` section which is a path to its agent configuration.

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

# Development

If you plan on extending or developing `platform_config.yml`, `configs/`, or the setup scripts in `core/`, build the
Docker image, "Dockerfile-dev", only once using `docker-compose -f docker-compose-dev.yml build --no-cache volttron1`.

Then start the container using `docker-compose -f docker-compose-dev.yml up`. When you want to make changes to "platform_config.yml", "configs/", or
"core/", simply make the changes and then rerun your container. You do not have to rebuild the image every time you make changes to those
aforementioned files and folders because they are mounted into the container. The only time you should rebuild the image is when
you make changes to the "volttron" source code since that is not mounted to the container but rather baked into the image during
the image build. Once you are satisfied your changes, update 'Dockerfile' with the changes you used in 'Dockerfile-dev' and submit a PR.

To set up your environment for development, do the following:

0. Give execute permissions for ./core/*
```
chmod a+x core/*
```

1. Pull in volttron from the [official volttron repo](https://github.com/VOLTTRON/volttron) using the following git command:

```bash
# Clones https://github.com/VOLTTRON/volttron.git into the 'volttron' directory
git submodule update --init --recursive
```

Why are we doing this? This repo has a directory called 'volttron', which contains the volttron codebase. In other words, this repo contains another repo in a subfolder.
When you initially clone this repo, the 'volttron' directory is empty. This directory contains the volttron codebase used to create the volttron platform.

OPTIONAL: This repo uses a specific version of volttron based on the commit in the 'volttron' submodule. If you want to use the latest volttron from the `develop`
branch from the volttron repo, execute the following command (NOTE: this is not required):

```bash
# Ensure that you are in the `volttron` folder
git pull origin develop
```

2. Build the image locally:

* Using docker-compose (preferred)
```bash
docker-compose -f docker-compose-dev.yml build --no-cache --force-rm
```

3. Run the container:

* Using docker-compose (preferred)
```
docker-compose -f docker-compose-dev.yml up
```

## Testing

If you want to work on improving/developing the Dockerfile, you can locally run a test script to check whether the image
works as expected. To run the test, see the following:

```bash
# builds a test image based on the Volttron version in '~/volttron' and runs tests
$ ./run-test-docker-image.sh

# You can also run the test but skip rebuilding the image
$ ./run-test-docker-image.sh -s
```

## Updating the image on Dockerhub

If you are not part of the Volttron Core development team, you can skip this section.

See: https://confluence.pnnl.gov/confluence/display/VNATION/Docker+Image+Publishing+Procedures

# Advanced Usage

In order for volttron to keep its state between runs, the state must be stored on the host.  We have attempted to make this as painless as possible, by using gosu to map the hosts UID onto the containers volttron user.  The following will create a directory to be written to during VOLTTRON execution.

1. Create a directory (eg `mkdir -p ~/vhome`).  This is where the VOLTTRON_HOME inside the container will be created on the host.
1. Start the docker container with a volume mount point and pass a LOCAL_USER_ID environmental variable.
    ``` bash
    docker run -e LOCAL_USER_ID=$UID -v /home/user/vhome:/home/volttron/.volttron -it volttron/volttron
    ```

In order to allow an external instance connect to the running volttron container one must add the -p <hostport>:<containerport> (e.g. 22916:22916)


# Troubleshooting

*My VC Platform agent can't connect to the Volttron Central address. I see `volttron.platform.vip.agent.subsystems.auth ERROR: Couldn't connect to https://localhost:8443 or incorrect response returned response was None` in the logs*

This most likely occurs if you are deploying this container behind a proxy. Ensure that your `~/.docker/config.json`
has no "proxies" configuration.

*My Forwarder shows a BAD status when I run `vctl status`*

Ensure that the configuration for your forwarder is using the same volttron-central-address property in volttron config, which is set in your platform_config.yml file.
