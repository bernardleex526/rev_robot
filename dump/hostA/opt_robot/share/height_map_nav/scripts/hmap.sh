#!/bin/bash
node_type=${1:-drdds}

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
echo "脚本路径: "
echo $SCRIPT_PATH

sleep 10
sudo taskset -c 4,5,6,7 $SCRIPT_PATH/../bin/height_map_nav

