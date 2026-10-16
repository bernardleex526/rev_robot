#!/bin/bash
#echo "loop_ap_start" >> /var/opt/robot/log/ap.log
# 定义接口名称
INTERFACE="wlan0"

# 无限循环，直到接口状态为“up”为止
while true; do
  # 使用 ip 命令检查接口状态
  status=$(ip link show "$INTERFACE" | grep "state UP")
  
  if [ -n "$status" ]; then
    #echo "$INTERFACE is up" >> /var/opt/robot/log/ap.log
    sleep 1
  else
    #echo "$INTERFACE is down, checking again in 5 second..." >> /var/opt/robot/log/ap.log
    /opt/robot/scripts/wifi/ap_start.sh stop
    sleep 1
    /opt/robot/scripts/wifi/ap_start.sh start 24G
    sleep 1
  fi
done

