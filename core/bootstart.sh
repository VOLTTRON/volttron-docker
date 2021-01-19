#! /usr/bin/env bash

# We are going to pre-setup the platform before running any of the environment.
if [[ -z /startup/setup-platform.py ]]; then
    echo "/startup/setup-platform.py does not exist.  The docker image must be corrupted"
    exit 1
fi

echo "Right before setup-platform.py is called I am calling printenv"
printenv

python3 /startup/setup-platform.py
setup_return=$?

if [[ $setup_return -ne 0 ]]; then
    echo "error running setup-platform.py"
    exit $setup_return
fi

echo "Setup of Volttron platform is complete."
echo "Starting Volttron..."

# Now spin up the volttron platform
volttron -vv
volttron_retcode=$?
if [[ $volttron_retcode ]]; then
  echo "volttron error"
  exit $volttron_retcode
fi
