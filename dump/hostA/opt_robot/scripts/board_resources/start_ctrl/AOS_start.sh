#!/bin/bash

echo "AOS starting"

PING_PARAMS="10.21.31.106"
RELEASE_NOTE_FILE="/var/opt/robot/release_note.json"


# 检查是否需要额外ping 10.21.31.104
if [ -f "$RELEASE_NOTE_FILE" ]; then
    # 文件存在，检查DEVICE_TYPE是否为PRO
    DEVICE_TYPE=$(grep -o '"DEVICE_TYPE"[[:space:]]*:[[:space:]]*"[^"]*"' "$RELEASE_NOTE_FILE" | sed 's/.*"DEVICE_TYPE"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
    if [ "$DEVICE_TYPE" = "PRO" ]; then
        PING_PARAMS="$PING_PARAMS 10.21.31.104"
        echo "DEVICE_TYPE is PRO, will ping both 10.21.31.106 and 10.21.31.104"
    else
        echo "DEVICE_TYPE is not PRO (found: $DEVICE_TYPE), will only ping 10.21.31.106"
    fi
else
    echo "Release note file not found at $RELEASE_NOTE_FILE, will only ping 10.21.31.106"
fi

/opt/robot/scripts/board_resources/start_ctrl/wait_net.sh "eth0" "eth1" "eth2" --ping  $PING_PARAMS

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
sleep 25
start_service "performance"

start_service "ctrlmcu"
start_service "gps_node"
start_service "cpunode"
#start_service "system_status"
start_service "yesense"

start_service "rl_deploy"
start_service "basic_server"

start_service "height_map_nav"
start_service "lio-perception"

sleep 5
start_service "rob_bag"

sleep 5
start_service "rsdriver"
start_service "hsLidar"


