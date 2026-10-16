#!/bin/bash
directory=$1
mode=$2

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
source $SCRIPT_PATH/../setup.bash
export LD_LIBRARY_PATH=/usr/local/lib/:/usr/local/lib/aarch64-linux-gnu:/usr/local/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
chmod 777 -R $directory         # give full permissions to the directory
chrt 49 taskset -c 4,5,6,7 $SCRIPT_PATH/../bin/slam_rosnode ${directory} $mode