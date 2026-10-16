#!/bin/bash
sleep 10
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
source $SCRIPT_PATH/../setup.bash
sudo chrt 35 taskset -c 4,5,6,7 $SCRIPT_PATH/../bin/lio_rosnode