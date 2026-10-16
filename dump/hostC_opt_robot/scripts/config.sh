#!/bin/bash
# 地图路径：
export MAPS_PATH="/var/opt/robot/data/maps/"

# 程序路径：
export PROGRAM_PATH=$(dirname "$(dirname "$(readlink -f "$0")")")

# ros版本：
export PROGRAM_VERSION="dds"   # dds, noetic

# 雷达类型：
export LIDAR_TYPE="Rslidar"   # Rslidar, Livox...
