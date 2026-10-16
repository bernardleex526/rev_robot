#!/bin/bash
sleep 10
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
echo "启动drdds节点"
sudo mkdir -p /var/opt/robot/data/maps/active
sudo chrt 35 taskset -c 5,6,7 $SCRIPT_PATH/../bin/lio_ddsnode