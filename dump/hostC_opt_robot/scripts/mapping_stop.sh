#!/bin/bash

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
source $SCRIPT_PATH/config.sh

# echo "debug 停止建图：脚本路径：$SCRIPT_PATH"



# map_path=$1

echo "结束额外程序"
bash $SCRIPT_PATH/extra_stop.sh

echo "结束建图程序"
# 判断程序版本是noetic还是dds
if [ $PROGRAM_VERSION = "noetic" ]; then
    source /opt/ros/noetic/setup.bash
fi
$SCRIPT_PATH/../bin/slam_command        # 编译过程区分的ros1和dds

sleep 1s

sudo systemctl stop mapping.service >/dev/null 2>&1
sudo systemctl reset-failed mapping.service >/dev/null 2>&1

chmod 777 -R $MAPS_PATH/active

# 检查地图文件full_cloud.pcd、occ_grid.yaml、occ_grid.pgm是否生成
# if [ -f "$map_path/full_cloud.pcd" ] && \
#    [ -f "$map_path/occ_grid.yaml" ] && \
#    [ -f "$map_path/occ_grid.pgm" ]; then
#    # 找到active软链接指向的实际目录
#     echo "地图生成成功。(Mapping successful.)：${map_path}"
# else
#     echo "地图生成失败，请尝试重新建图。(Mapping failed. Please try again.)"
# fi

# echo "重启定位程序"
# sudo systemctl restart localization.service >/dev/null 2>&1


# sudo systemctl restart localization.service >/dev/null 2>&1

SERVICE_NAME="localization"
if systemctl list-unit-files --type=service | grep -qw "$SERVICE_NAME"; then
    echo "服务 $SERVICE_NAME 存在于系统中。进行重启"
    sudo systemctl restart $SERVICE_NAME >/dev/null 2>&1
fi

# echo "重启htx程序"
SERVICE_NAME="htx_nav"
if systemctl list-unit-files --type=service | grep -qw "$SERVICE_NAME"; then
    echo "服务 $SERVICE_NAME 存在于系统中。进行重启"
    sudo systemctl restart $SERVICE_NAME >/dev/null 2>&1
fi

SERVICE_NAME="planner"
if systemctl list-unit-files --type=service | grep -qw "$SERVICE_NAME"; then
    echo "服务 $SERVICE_NAME 存在于系统中。进行重启"
    sudo systemctl restart $SERVICE_NAME >/dev/null 2>&1
fi