#!/bin/bash
node_type=${1:-drdds}

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
echo "脚本路径: "
echo $SCRIPT_PATH

if [ $node_type = "drdds" ]
then
	echo "启动drdds节点"
    sudo mkdir -p /var/opt/robot/record/maps/active
    sudo rm -rf /var/opt/robot/record/maps/active/blocks
    sudo chrt 49 taskset -c 4,5,6,7 $SCRIPT_PATH/../bin/lio_ddsnode
elif [ $node_type = "ros1" ]
then
	echo "启动ros1节点"
    source $SCRIPT_PATH/../setup.bash
    # sudo chrt 90 taskset -c 4,5,6,7 $SCRIPT_PATH/../bin/lio_rosnode
    $SCRIPT_PATH/../bin/lio_rosnode
else
	echo "请指定正确的参数【drdds, ros1, ros2】"
fi