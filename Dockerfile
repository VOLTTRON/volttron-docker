ARG image_user=amd64
ARG image_repo=debian
ARG image_tag=buster

FROM ${image_user}/${image_repo}:${image_tag} as volttron_base

SHELL [ "bash", "-c" ]

ENV OS_TYPE=debian
ENV DIST=buster
ENV VOLTTRON_GIT_BRANCH=rabbitmq-volttron
ENV VOLTTRON_USER_HOME=/home/volttron
ENV VOLTTRON_HOME=${VOLTTRON_USER_HOME}/.volttron
ENV CODE_ROOT=/code
ENV VOLTTRON_ROOT=${CODE_ROOT}/volttron
ENV VOLTTRON_USER=volttron
ENV USER_PIP_BIN=${VOLTTRON_USER_HOME}/.local/bin
ENV RMQ_ROOT=${VOLTTRON_USER_HOME}/rabbitmq_server
ENV RMQ_HOME=${RMQ_ROOT}/rabbitmq_server-3.7.7

USER root

RUN set -eux; apt-get update; apt-get install -y --no-install-recommends \
    procps \
    gosu \
    vim \
    tree \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    openssl \
    libssl-dev \
    libevent-dev \
    git \
    gnupg \
    dirmngr \
    apt-transport-https \
    wget \
    curl \
    ca-certificates \
    libffi-dev \
    sqlite3

# Set default 'python' to 'python3'
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Set default 'pip' to 'pip3'
RUN ln -s /usr/bin/pip3 /usr/bin/pip

# Create a user called 'volttron'
RUN id -u $VOLTTRON_USER &>/dev/null || adduser --disabled-password --gecos "" $VOLTTRON_USER

RUN mkdir -p /code && chown $VOLTTRON_USER.$VOLTTRON_USER /code && \
    echo "export PATH=/home/volttron/.local/bin:$PATH" > /home/volttron/.bashrc

############################################
# ENDING volttron_base stage
# Creating volttron_core stage
############################################
FROM volttron_base AS volttron_core

# copy over /core, i.e. the custom startup scripts for this image
RUN mkdir /startup $VOLTTRON_HOME && \
    chown $VOLTTRON_USER.$VOLTTRON_USER $VOLTTRON_HOME
COPY ./core /startup
RUN chmod +x /startup/*

# copy over volttron repo
USER $VOLTTRON_USER
COPY --chown=volttron:volttron volttron /code/volttron
WORKDIR /code/volttron
RUN pip install -e . --user --extra-index-url https://www.piwheels.org/simple
RUN echo "package installed at `date`"

############################################
# RABBITMQ SPECIFIC INSTALLATION
############################################
# the ARG install_rmq must be declared twice due to scope; see https://docs.docker.com/engine/reference/builder/#using-arg-variables
USER root
ARG install_rmq
RUN if [ "${install_rmq}" = "false" ] ; then \
      echo "Not installing RMQ dependencies.";  \
    else \
      ./scripts/rabbit_dependencies.sh $OS_TYPE $DIST && \
      python -m pip install gevent-pika --extra-index-url https://www.piwheels.org/simple; \
    fi

USER $VOLTTRON_USER
ARG install_rmq
RUN if [ "${install_rmq}" = "false" ] ; then \
      echo "Not installing RMQ"; \
    else \
      mkdir $RMQ_ROOT && \
      set -eux && \
      wget -P $VOLTTRON_USER_HOME https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.7.7/rabbitmq-server-generic-unix-3.7.7.tar.xz && \
      tar -xf $VOLTTRON_USER_HOME/rabbitmq-server-generic-unix-3.7.7.tar.xz --directory $RMQ_ROOT && \
      $RMQ_HOME/sbin/rabbitmq-plugins enable rabbitmq_management rabbitmq_federation rabbitmq_federation_management rabbitmq_shovel rabbitmq_shovel_management rabbitmq_auth_mechanism_ssl rabbitmq_trust_store;  \
    fi
############################################


########################################
# The following lines should be run from any Dockerfile that
# is inheriting from this one as this will make the volttron
# run in the proper location.
#
# The user must be root at this point to allow gosu to work
########################################
USER root
WORKDIR ${VOLTTRON_USER_HOME}
ENTRYPOINT ["/startup/entrypoint.sh"]
CMD ["/startup/bootstart.sh"]
