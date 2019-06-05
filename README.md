# Official VOLTTRON docker image

# Introduction

This image provides a reproducable way to install VOLTTRON within a docker container.
By using a volume mount of the `VOLTTRON_HOME` directory, runtime changes made by the platform are visible on the host and are preserved across instances of the container.
Similarly, changes made from the host are reflect in the container.
The image features gosu, which allows the non-root user executing the volttron platform inside the container to have the same UID as the host user running the container on the host system.
In conjection with volume mounting of the directory, this ensures that file ownership and permissions in `VOLTTRON_HOME` match the host user, avoiding cases were root in the container leaves files inaccessible to a user without sudo permissions on the host.

# Platform Initialization

The VOLTTRON container when created is just a blank container with no agents.  Now there is an initialization routine available within the docker container to allow the installation of agents before launching of the instance.  To do this one will mount a `platform_config.yml` file to `/platform_config.yml` within the container. One is also likely to need to mount agent configurations (specified in the `platform_config.yml` file), into the container. The recommended way to do this is through a `docker-compose.yml` file.  An example of this is included in this repository, based on the one in the [volttron-fuel-cells repo](https://github.com/VOLTTRON/volttron-fuel-cells/).

The `platform_config.yml` file has two sections: `config`, which configures the main instance and populate's the main config file ($VOLTTRON_HOME/config), and `agents`, which contains a list of agents with references to configurations for them (note the frequent use of environment variables in this section).

## Main Configuration
The main instance configuration is composed of key value pairs under a "config" key in the `platofrom_config.yml` file.
As an example, the `vip-address` and `bind-web-address` would be populated using the following partial file:
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
The agent configuration section is under a top-level key "agents" and contains several layers of nested key-value mappings.
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
agents within the `platform_config.yml` file are created sequentailly, it can take several seconds for each to spin up and be visible via `vctl` commands.

# Raw Container Usage

``` bash
# Retrieves and executes the volttron container.
docker run -it volttron/volttron
```

After entering the above command the shell will be within the volttron container as a user named volttron.

``` bash
# starting the platform
volttron -vv -l volttron.log&

# cd to volttron root
cd $VOLTTRON_ROOT

# installing listener agent
python scripts/core/make-listener

# see the log messages
tail -f volttron.log
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
