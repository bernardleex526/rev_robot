#!/bin/bash

map_path=$1

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
source $SCRIPT_PATH/config.sh

# 判断程序版本是noetic还是dds
if [ $PROGRAM_VERSION = "dds" ]; then
    if [ -f "/home/user/latest_HTX/offline_topology_builder/build/run_offline" ]; then
        /home/user/latest_HTX/offline_topology_builder/build/run_offline $map_path/.nav_maps/nav_map_0/passable_tmp/ $map_path/.nav_maps/nav_map_0/top_map/ $map_path/.sessions/session_0/poses.txt
    fi
elif [ "$PROGRAM_VERSION" = "noetic" ]; then
    if [ -f "/home/ysc/latest_HTX/offline_topology_builder/build/run_offline" ]; then
        /home/ysc/latest_HTX/offline_topology_builder/build/run_offline $map_path/.nav_maps/nav_map_0/passable_tmp/ $map_path/.nav_maps/nav_map_0/top_map/ $map_path/.sessions/session_0/poses.txt
    fi
else
    echo "${RED}[ERROR] 未知的ROS版本参数：${PROGRAM_VERSION}${RESET}"
fi

echo "完成额外的后处理程序"