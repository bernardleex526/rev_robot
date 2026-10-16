#!/bin/bash
node_type=${1:-drdds}

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
echo "脚本路径: "
echo $SCRIPT_PATH

# 确保目录存在
sudo mkdir -p /var/opt/robot/log/system
sudo chmod 755 /var/opt/robot/log/system
# 设置coredump
# sudo bash -c "ulimit -c unlimited"
# sudo bash -c "echo '/var/opt/robot/log/system/coredump.%e.%p.%t' > /proc/sys/kernel/core_pattern"

sudo chrt 45 taskset -c 6,7 $SCRIPT_PATH/../bin/astar_node
