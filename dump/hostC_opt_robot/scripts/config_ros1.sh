#!/bin/bash
# 地图路径：
export MAPS_PATH="/home/ysc/jy_cog/system/maps/"

# 程序路径：
export PROGRAM_PATH=$(dirname "$(dirname "$(readlink -f "$0")")")

# ros版本：
export PROGRAM_VERSION="noetic"   # foxy, noetic

# 雷达类型：
export LIDAR_TYPE="Livox"   # Robosense, Livox...
