#!/bin/bash

# Add local user
# Either use the LOCAL_USER_ID if passed in at runtime or
# fallback
set -e

USER_ID="${LOCAL_USER_ID:?LOCAL_USER_ID must be set use -e LOCAL_USER_ID=\$UID -it <image> as an example}" # ${LOCAL_USER_ID:-2001}

if [[ -z ${USER_ID} ]]; then
  echo "USER_ID NOT SET"
  echo "Please pass environmental variable LOCAL_USER_ID to the run command."
  echo "docker run -e LOCAL_USER_ID=\$UID -it <image> as an example."
  exit 1
fi

# The HOME directory is not setup in the docker context yet
# we need that to be setup before we call the main startup script.
export HOME=${VOLTTRON_USER_HOME}

# Add the pip user bin to the path since we aren't using the
# virtualenv environment in the distribution.
export PATH=$HOME/.local/bin:$PATH
VOLTTRON_UID_ORIGINAL=`id -u volttron`

echo "original volttron uuid is $VOLTTRON_UID_ORIGINAL"

if [[ $VOLTTRON_UID_ORIGINAL != $USER_ID ]]; then
  echo "Changing volttron USER_ID to match passed LOCAL_USER_ID ${USER_ID} "
  usermod -u $USER_ID volttron
fi

# # Only need to change
# if [ -z "${VOLTTRON_USER_HOME}" ]; then
echo "chown volttron.volttron -R $VOLTTRON_USER_HOME"
chown volttron.volttron -R ${VOLTTRON_USER_HOME}
# fi


if [[ $# -lt 1 ]]; then
  echo "Please provide a command to run (e.g. /bin/bash, volttron -vv)";
  exit 1;
else
  echo "now Executing $@";
  #chroot --userspec volttron ${VOLTTRON_ROOT} "$@";
  exec gosu volttron "$@";
fi
