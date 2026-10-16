#!/bin/bash

# 读取 /opt/robot/os_type 文件内容
os_type=$(cat /opt/robot/os_type 2>/dev/null)

if [ "$os_type" = "CA9B_AOS" ]; then
    echo "OS type is CA9B_AOS"
    sudo /opt/robot/scripts/board_resources/start_ctrl/AOS_start.sh
elif [ "$os_type" = "CA9B_NOS" ]; then
    echo "OS type is CA9B_NOS"
    sudo /opt/robot/scripts/board_resources/start_ctrl/NOS_start.sh
elif [ "$os_type" = "CA9B_GOS" ]; then
    echo "OS type is CA9B_GOS"
    sudo /opt/robot/scripts/board_resources/start_ctrl/GOS_start.sh
else
    echo "OS type is not find, it is: $os_type"
    exit -1
fi