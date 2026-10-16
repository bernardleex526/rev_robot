#!/bin/bash
sleep 5
/opt/robot/scripts/wifi/wifi_ctl.sh enable
sleep 1
/opt/robot/scripts/wifi/wifi_ctl.sh disable
sleep 1
/opt/robot/scripts/wifi/wifi_ctl.sh enable
sleep 1
# 循环检查 /sys/class/net/wlan0 是否存在
while true; do
    if [ -d "/sys/class/net/wlan0" ]; then
        echo "wlan0 启动成功 "
	sleep 1
    else
	    /opt/robot/scripts/wifi/wifi_ctl.sh disable
	    sleep 1
	    echo "wlan0 重启"
	    /opt/robot/scripts/wifi/wifi_ctl.sh enable
    fi
    sleep 5  # 等待一秒
done
