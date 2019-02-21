#! /usr/bin/env bash

source ${VOLTTRON_ROOT}/env/bin/activate
python /startup/setup-platform.py
PID=$?

if [ "$PID" == "0" ]; then
    echo "Starting volttron itself"
    volttron -vv
fi
