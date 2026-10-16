#!/bin/bash
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
source $SCRIPT_PATH/config.sh

# 检查参数个数
if [ $# -ne 1 ]; then
    echo "错误：需要指定编号"
    echo "用法: $0 <编号>"
    exit 1
fi

# 检查参数是否为整数
if [[ $1 =~ ^-?[0-9]+$ ]]; then
    echo "准备指定编号 '$1' "
else
    echo "错误：编号 '$1' 不是有效的整数"
    exit 1
fi

sudo /opt/robot/share/slam/bin/slam_set_label $1