#!/bin/bash

echo "GOS starting"

/opt/robot/scripts/board_resources/start_ctrl/wait_net.sh "eth0"

# 定义启动服务的函数
start_service() {
    local service_name="$1"
    echo "Starting service: $service_name..."
    
    # 尝试启动服务
    if sudo systemctl restart "$service_name.service"; then
        echo "Successfully started service: $service_name"
    else
        echo "Failed to start service: $service_name"
    fi
}
sleep 3
start_service "performance"

start_service "encryption_node"
start_service "cpunode"
#start_service "system_status"
start_service "uwb_node"
start_service "rsdriver"
start_service "hsLidar"
