# Quick Reference

* Maintained by: [The Volttron Team](mailto:volttron@pnnl.gov)
* Where to get help: [Stack Overflow](http://stackoverflow.com/questions/tagged/volttron)
* Where to file issues: [Volttron-Docker issues](https://github.com/VOLTTRON/volttron-docker/issues)
* Supported architectures: [amd64/debian](https://hub.docker.com/r/amd64/debian)

# Supported tags and respective Dockerfile links
* [latest, >1.0, develop](https://github.com/VOLTTRON/volttron-docker/blob/main/Dockerfile)

# Introduction

VOLTTRON™ is an open source, scalable, and distributed platform that seamlessly integrates data, devices, and systems for sensing and control applications. It is built on extensible frameworks allowing contributors to easily expand the capabilities of the platform to meet their use cases. Features are implemented as loosely coupled software components, called agents, enabling flexible deployment options and easy customization.
For more information, read [our documentation](https://volttron.readthedocs.io/en/develop/index.html).

This image provides a reproducible way to install VOLTTRON within a docker container.
The image uses the utility [gosu](https://github.com/tianon/gosu), which allows the non-root user executing the volttron platform inside the container to have the same UID as the host user running the container on the host system.

# How to use this image

## Using docker

### Prerequisites

* You must create a Docker volume before your run your container. The Docker volume that you create will be used
as a volume (i.e. volume-mounted) in your Docker run command to persist the Volttron platform database.
  * To create this volume, run the following command:`docker volume create volttron1-data`

* You must create a `platform_config.yml` that will describe your Volttron platform configuration and the agents that you want installed. For an example, see [volttron-docker/platform.config](https://github.com/VOLTTRON/volttron-docker/blob/main/platform_config.yml). This file will be bind-mounted into your container. Below is an example of such a configuration file:
```shell
# Properties to be added to the root config file
# the properties should be ingestible for volttron
# the values will be presented in the config file
# as key=value
config:
  vip-address: tcp://0.0.0.0:22916
  # For rabbitmq this should match the hostname specified in
  # in the docker compose file hostname field for the service.
  bind-web-address: https://0.0.0.0:8443
  volttron-central-address: https://0.0.0.0:8443
  instance-name: volttron1
  message-bus: zmq # allowed values: zmq, rmq
  # volttron-central-serverkey: a different key

# Agents dictionary to install. The key must be a valid
# identity for the agent to be installed correctly.
agents:

  # Each agent identity.config file should be in the configs
  # directory and will be used to install the agent.
  listener:
    source: $VOLTTRON_ROOT/examples/ListenerAgent
    config: $CONFIG/listener.config
    tag: listener
```

* You must create a `volttron_configs` directory that will hold all your agent configurations. For an example of what files can be put in this directory, see [volttron-docker/configs](https://github.com/VOLTTRON/volttron-docker/tree/main/configs). This directory will be bind-mounted into your container.

After you have completed all the prerequisites, you can now run the container. NOTE: You need to ensure that the source paths for
your bind mounts (i.e. your local version of platform_config.yml and the directory volttron_configs) are properly created. In the following example,
the file and directory are placed in the working directory denoted by `pwd`:

```shell
docker run \
--name volttron1 \
--hostname volttron1 \
-p 8443:8443 \
--env CONFIG=/home/volttron/configs \
--env LOCAL_USER_ID=1000 \
--mount type=bind,source="$(pwd)/platform_config.yml",target=/platform_config.yml \
--mount type=bind,source="$(pwd)/volttron_configs",target=/home/volttron/configs \
--mount type=volume,source=volttron1-data,target=/home/volttron/db \
eclipsevolttron/volttron:v3.0
```

## Using docker-compose

If you don't want to type a long `docker run` command every time you run a container, you can wrap your command in a
docker-compose script. See this example from (docker-compose.yml)[https://github.com/VOLTTRON/volttron-docker/blob/main/docker-compose.yml].
Note that you still need to ensure that the paths to the bind-mounts are properly constructed. After you create your docker-compose script,
simply run `docker-compose run` in the same directory that holds your script.

```shell
version: '3.4'

services:
  volttron1:
    container_name: volttron1
    hostname: volttron1
    image: eclipsevolttron/volttron:v3.0
    ports:
      # host_port:container_port
      # http port for volttron central
      - 8443:8443
    volumes:
      - ./platform_config.yml:/platform_config.yml
      - ./configs:/home/volttron/configs
      - volttron1-volume:/home/volttron/db
    environment:
      - CONFIG=/home/volttron/configs
      - LOCAL_USER_ID=1000

volumes:
  volttron1-volume:
    name: volttron1-data
```

## Container shell access

The `docker exec` command allows you to run commands inside a Docker container. The following command line will give you a bash shell inside your `volttron1` container:

```shell
docker exec -itu volttron volttron1 bash
```

## Environment Variables

When you start a Volttron image, you can adjust two environment variables:

```shell
CONFIG
```

This is the path on the Volttron docker container to the directory that holds the agent configuration files of all the agents that you automagically
want installed. Recall that these agents are listed in your `platform_config.yml`. Note that this path is used as the
destination path for the bind-mount for the local `volttron_configs` directory mentioned previously. Thus, you need to ensure
that the value for this environment variable matches the destination path in that bind mount. We recommend using `/home/volttron/configs` as the destination path on your container.

```shell
LOCAL_USER_ID
```

The UID of the host machine that is running the container. We recommend using `1000`.
