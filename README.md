# Official VOLTTRON docker image

# Introduction
This image provides a reproducable way to install VOLTTRON within a docker container.  It features gosu which allows the storage of VOLTTRON_HOME to be persistable on the hosts hard drive.  The
base docker images are available on docker hub at https://hub.docker.com/r/volttron/volttron/.

# Usage

```` bash
# Retrieves and executes the volttron container.
docker run -it volttron/volttron
````

After entering the above command the shell will be within the volttron container as a user named volttron.

```` bash
# starting the platform
volttron -vv -l volttron.log&

# cd to volttron root
cd $VOLTTRON_ROOT

# installing listener agent
python scripts/core/make-listener

# see the log messages
tail -f volttron.log
````

All the same functionality that one would have from a VOLTTRON command line is available through the container.

# Platform Initialization

The VOLTTRON container when created is just a blank container with no agents.  Now there is an initialization routine available within the docker container to allow the installation of agents before launching of the instance.  To do this one will mount a platform_config.yml file to /platform_config.yml.  The recommended way to do this is through a docker-compose.yml file.  An example of this is available https://github.com/VOLTTRON/volttron-fuel-cells/.

# Advanced Usage

In order for volttron to keep its state between runs, the state must be stored on the host.  We have attempted to make this as painless as possible, by using gosu to map the hosts UID onto the containers volttron user.  The following will create a directory to be written to during VOLTTRON execution.

1. Create a directory (mkdir -p vhome).  This is where the VOLTTRON_HOME inside the container will be created on the host.
1. Start the docker container with a volume mount point and pass a LOCAL_USER_ID environtmental variable.
    ```` bash
    docker run -e LOCAL_USER_ID=$UID -v /home/user/vhome:/home/volttron/.volttron -it volttron/volttron
    ````

In order to allow an external instance connect to the running volttron container one must add the -p <hostport>:<containerport> (e.g. 22916:22916)

