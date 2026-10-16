#!/bin/bash

if [ -f /opt/robot/os_type ]; then
    os_type=$(cat /opt/robot/os_type)
    if [ "$os_type" = "CA9B_VOS" ]; then
        echo "os_type=$os_type, 脚本直接退出"
        exit 1
    fi
    if [ "$os_type" = "CA9B_GOS" ]; then
        echo "os_type=$os_type, 脚本直接退出"
        exit 1
    fi
    if [ "$os_type" = "CA9B_NOS" ]; then
        echo "os_type=$os_type, 脚本直接退出"
        exit 1
    fi
fi

cd /opt/robot/scripts/board_resources/rtsp_service
sudo ./mediamtx &
sleep 5
# =============================================================================
# 等待系统时间同步 (避免 NTP 同步在推流中途跳变导致 RTSP 连接中断)
# 问题: 板子 RTC 丢失时启动后初始时间为 2024, NTP 同步会使系统时钟跳变几年,
#       这会击潰 rtspclientsink 的 TCP 长连接, mediamtx 连接被关闭
# =============================================================================
wait_time_sync() {
    local max_wait=60
    local count=0
    echo "等待系统时间同步..."
    # 优先用 timedatectl 检测
    while [ ${count} -lt ${max_wait} ]; do
        if command -v timedatectl >/dev/null 2>&1; then
            if timedatectl status 2>/dev/null | grep -q "System clock synchronized: yes"; then
                echo "时间已同步 (timedatectl)"
                return 0
            fi
        fi
        # 备选: 检测年份是否合理 (大于 2025)
        local year=$(date +%Y)
        if [ "${year}" -ge 2025 ] 2>/dev/null; then
            echo "时间已同步 (year=${year})"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    echo "警告: 等待 ${max_wait}s 后仍未同步时间, 继续启动推流"
    return 1
}
wait_time_sync
/opt/robot/scripts/board_resources/rtsp_service/push_video.sh
