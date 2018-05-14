#!/bin/bash

# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or
# fallback
set -e
USER_ID=${LOCAL_USER_ID:-9001}

echo "Starting with UID : $USER_ID VOLTTRON_USER_HOME is $VOLTTRON_USER_HOME"
#useradd --shell /bin/bash -u $USER_ID -o -c "" -m volttron
usermod -u $USER_ID volttron

export HOME=${VOLTTRON_USER_HOME}

# Only need to change
if [ -z "${VOLTTRON_USER_HOME}" ]; then
  chown volttron.volttron -R ${VOLTTRON_USER_HOME}
fi

cd ${VOLTTRON_USER_HOME}
echo "now Executing $@"
exec /usr/local/bin/gosu volttron "$@"
