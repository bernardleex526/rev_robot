#!/bin/bash
map_path=$1
# 建图开始后执行内容
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
source $SCRIPT_PATH/config.sh

mkdir -p $map_path/.nav_maps/nav_map_0/passable_tmp/
mkdir -p $map_path/.nav_maps/nav_map_0/top_map/

if [ $PROGRAM_VERSION = "dds" ]; then
    if [ -f "/home/user/latest_HTX/keyframe_saver_ws/scripts/saver_start.sh" ]; then
        chmod 777 /home/user/latest_HTX/keyframe_saver_ws/scripts/saver_start.sh
        sudo systemd-run --unit=keyframe_saver /home/user/latest_HTX/keyframe_saver_ws/scripts/saver_start.sh $map_path/.nav_maps/nav_map_0/passable_tmp/
    fi
elif [ "$PROGRAM_VERSION" = "noetic" ]; then
    
    if [ -f "/home/ysc/latest_HTX/keyframe_saver_ws/scripts/saver_start.sh" ]; then
        chmod 777 /home/ysc/latest_HTX/keyframe_saver_ws/scripts/saver_start.sh
        sudo systemd-run --unit=keyframe_saver /home/ysc/latest_HTX/keyframe_saver_ws/scripts/saver_start.sh $map_path/.nav_maps/nav_map_0/passable_tmp/
    fi
else
    echo "${RED}[ERROR] 未知的程序版本参数：${PROGRAM_VERSION}${RESET}"
fi
