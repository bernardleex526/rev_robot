#!/bin/bash

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
# echo "debug $SCRIPT_PATH"
source $SCRIPT_PATH/config.sh

# 停止外部相关程序
#sudo systemctl stop htx_nav.service
#sudo systemctl reset-failed htx_nav.service
SERVICE_NAME="localization"
if systemctl list-unit-files --type=service | grep -qw "$SERVICE_NAME"; then
    echo "服务 $SERVICE_NAME 存在于系统中。"

    # 2. (可选)检查服务是否已经在运行
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "关闭正在运行的 $SERVICE_NAME 服务。"
        sudo systemctl stop $SERVICE_NAME.service
        sudo systemctl reset-failed $SERVICE_NAME.service
    fi
fi

SERVICE_NAME="htx_nav"
if systemctl list-unit-files --type=service | grep -qw "$SERVICE_NAME"; then
    echo "服务 $SERVICE_NAME 存在于系统中。"

    # 2. (可选)检查服务是否已经在运行
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "关闭正在运行的 $SERVICE_NAME 服务。"
        sudo systemctl stop $SERVICE_NAME.service
        sudo systemctl reset-failed $SERVICE_NAME.service
    fi
fi


# 停止已开启的建图程序
if pgrep -x "slam_ddsnode" > /dev/null; then
    echo "已有执行中的建图程序，停止并保存. The mapping program is already running. Save and exit..."
    bash $SCRIPT_PATH/mapping_stop.sh
fi
# 检查临时单元是否存在
if systemctl list-units --type=service --all | grep -q "mapping\.service"; then
    # echo "[状态] mapping.service 存在"
    sudo systemctl stop mapping.service >/dev/null 2>&1
    sudo systemctl reset-failed mapping.service >/dev/null 2>&1
fi


# 初始化ght
# 设置超时时间（秒）
TIMEOUT=4
echo "正在检查视觉RTK增强功能是否可用..."

# 判断程序版本是noetic还是dds
if [ $PROGRAM_VERSION = "dds" ]; then
    source /home/user/fibocom_ws/install/setup.bash
    if ping -c 1 10.21.31.10 &> /dev/null; then
        # 调用服务并获取输出[6](@ref)
        ros2 service call /fibo_fusion_interface fibocom_msgs/srv/FiboFusionInterface cmd:\ 11\ 
        echo "视觉RTK增强功能可用"
        break
    else
        sleep 1
        count=$((count + 1))
        echo "视觉RTK增强功能不可用"
    fi
elif [ "$PROGRAM_VERSION" = "noetic" ]; then
    source /home/ysc/fibocom_ws/devel/setup.bash
    if ping -c 1 10.21.31.10 &> /dev/null; then
        # 调用服务并获取输出[6](@ref)
        rosservice call /fibo_fusion_interface cmd: "11"
        echo "视觉RTK增强功能可用"
        break
    else
        sleep 1
        count=$((count + 1))
        echo "视觉RTK增强功能不可用"
    fi
else
    echo "${RED}[ERROR] 未知的ROS版本参数：${PROGRAM_VERSION}${RESET}"
fi