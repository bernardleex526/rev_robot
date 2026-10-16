#!/bin/bash

echo "NOS starting"

/opt/robot/scripts/board_resources/start_ctrl/wait_net.sh "eth0" "eth1"  --ping 10.21.31.103

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
sleep 15

start_service "performance"

start_service "cpunode"
#start_service "system_status"
start_service "yesense"

sleep 15
start_service "charge_manager"
start_service "reflective_column"

start_service "handler"

start_service "localization"
sleep 5

start_service "passable_area"
start_service "global_planner"
start_service "planner"

sleep 5
start_service "rsdriver"
start_service "hsLidar"
