#!/bin/bash

XML_FILE="/opt/robot/fastdds.xml"

# 检查 XML 文件是否存在
if [ ! -f "$XML_FILE" ]; then
    echo "Error: $XML_FILE not found"
    exit 1
fi

###############################################################################
# 1️⃣ 明确：判断逻辑只依赖 eth0 的“单一 IP”
###############################################################################

ETH0_IP=$(ip -4 addr show eth0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1)

if [ -z "$ETH0_IP" ]; then
    echo "Error: Could not detect eth0 IPv4 address"
    exit 1
fi

echo "Detected eth0 IP: $ETH0_IP"

###############################################################################
# 2️⃣ 从 eth0 IP 中解析最后一段（绝对安全）
###############################################################################

LAST_SEGMENT="${ETH0_IP##*.}"

###############################################################################
# 3️⃣ 根据 eth0 IP 的最后一段，决定要写入的 IP_LIST
###############################################################################

case "$LAST_SEGMENT" in
    103)
        IP_LIST="10.21.33.103"
        ;;
    106)
        IP_LIST="10.21.33.106 "
        ;;
    104)
        IP_LIST="10.21.31.104"
        ;;
    *)
        echo "Unknown eth0 IP last segment: $LAST_SEGMENT"
        IP_LIST="$ETH0_IP"
        ;;
esac

echo "Selected IP(s) based on eth0 IP ($ETH0_IP): $IP_LIST"

###############################################################################
# 4️⃣ 写入 fastdds.xml（幂等）
###############################################################################

for ip in $IP_LIST; do
    if grep -q "<address>${ip}</address>" "$XML_FILE"; then
        echo "IP ${ip} already exists in $XML_FILE"
    else
        sudo sed -i "/<\/interfaceWhiteList>/i \                <address>${ip}<\/address>" "$XML_FILE"
        echo "Inserted <address>${ip}</address> into $XML_FILE"
    fi
done

###############################################################################
# 5️⃣ ROS 2 环境
###############################################################################

if [ -n "$ROS_DISTRO" ]; then
    echo "Current ROS_DISTRO is $ROS_DISTRO"
    source /opt/ros/$ROS_DISTRO/setup.bash
else
    source /opt/ros/foxy/setup.bash
fi

export FASTRTPS_DEFAULT_PROFILES_FILE=/opt/robot/fastdds.xml
echo "source ros2 env success"
