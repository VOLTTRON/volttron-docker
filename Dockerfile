FROM alpine
ARG PGID=1500
ARG PUID=1500
ARG GIT_USER=VOLTTRON
ARG GIT_BRANCH=releases/5.0rc
ARG USER=volttron

RUN addgroup -g ${PGID} ${USER} && \
    adduser -D -u ${PUID} -G ${USER} ${USER}

RUN apk update \
    && apk add ca-certificates wget openssl openssl-dev \
     linux-headers unzip python-dev libevent-dev build-base gcc \
    && update-ca-certificates 
    
USER volttron

RUN cd /home/volttron \
    && wget https://github.com/${GIT_USER}/volttron/archive/${GIT_BRANCH}.zip -O volttron.zip \
    && unzip volttron.zip \
    && mv ${USER}-${GIT_BRANCH/\//-} volttron \
    && cd /home/volttron/volttron \
    && python bootstrap.py

WORKDIR /home/volttron/volttron

