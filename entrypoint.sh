#!/bin/bash

# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or
# fallback
set -e
USER_ID=${LOCAL_USER_ID:-9001}

echo "Starting with UID : $USER_ID"
#useradd --shell /bin/bash -u $USER_ID -o -c "" -m volttron
usermod -u $USER_ID volttron

export HOME=/home/volttron
chown volttron.volttron -R /home/volttron
echo "now Executing $@"
exec /usr/local/bin/gosu volttron "$@"