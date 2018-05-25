#! /usr/bin/env bash

source ${VOLTTRON_ROOT}/env/bin/activate
echo "RUNNING BOOTSTART"
python /startup/setup-platform.py
PID=$?
echo "the pid is $PID"
if [ "$PID" == "0" ]; then
    volttron -vv
fi
