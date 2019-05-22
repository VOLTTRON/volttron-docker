#! /usr/bin/env bash

# Uncomment if we are going to pre-setup the platform before
# running any of the environment.
if [[ -z /startup/setup-platform.py ]]; then
    echo "/startup/setup-platform.py does not exist.  The docker image must be corrupted"
    exit 1
fi

echo "Right before setup-platform.py is called I am calling printenv"
printenv
python /startup/setup-platform.py
setup_return=$?
if [[ $setup_return ]]; then
    echo "error running setup-platform.py"
    exit $setup_return
fi

# TODO
# does setup-playtform.py return its PID? or do you not mean PID?
# should `volttron -vv` be run if setup-platform fails?

#PID=$?
#echo "PID WAS $PID"
#if [[ "$setup_return" == "0" ]]; then
    volttron -vv
    volttron_retcode=$?
#fi
if [[ $volttron_retcode ]]; then
  echo "volttron error"
  exit $volttron_retcode
fi
