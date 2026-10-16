#!/bin/bash
directory=$1
mode=$2

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
export LD_LIBRARY_PATH=/usr/local/lib/:/usr/local/lib/aarch64-linux-gnu:$LD_LIBRARY_PATH
chrt 49 taskset -c 4,5,6,7 $SCRIPT_PATH/../bin/slam_ddsnode ${directory} $mode