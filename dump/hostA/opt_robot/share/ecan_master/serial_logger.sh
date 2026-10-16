#!/usr/bin/env bash
set -euo pipefail

# 当前时间
YYYY_MMDD=$(date "+%Y_%m%d")

# 检查机器人类型
DEVICES=$(grep '^ecan_uart_port' /var/opt/robot/conf/HWI.toml \
    | sed -E 's/.*=\s*\[(.*)\]/\1/' \
    | tr -d '"' \
    | tr ',' ' ')

if [[ -z "$DEVICES" ]]; then
    echo "[serial-logger] ERROR: 未在 /var/opt/robot/conf/HWI.toml 中找到 ecan_uart_port 配置" >&2
    exit 1
fi

BAUD="115200"
LOGDIR="/var/opt/robot/log/$YYYY_MMDD"

mkdir -p "$LOGDIR"

for DEVICE in $DEVICES; do
    PORT=$(basename "$DEVICE")
    LOGFILE="$LOGDIR/${PORT}_${YYYY_MMDD}.log"

    # 醒目的重启标识
    {
        echo
        echo "################################################################################"
        echo "################################################################################"
        echo "################################################################################"
        echo "### [serial-logger] === Service Restarted at $(date '+%Y-%m-%d %H:%M:%S') ==="
        echo "### Logging $DEVICE -> $LOGFILE (baud=115200)" >> "$LOGFILE"
        echo "################################################################################"
        echo "################################################################################"
        echo "################################################################################"
        echo
    } >> "$LOGFILE"

    # 设置串口参数：8N1，无流控，原始模式
    stty -F "$DEVICE" 115200 cs8 -parenb -cstopb -crtscts -ixon -ixoff -echo raw

    # 后台启动 cat，将输出实时写入日志文件
    stdbuf -o0 -e0 cat "$DEVICE" >> "$LOGFILE" &
done

wait
