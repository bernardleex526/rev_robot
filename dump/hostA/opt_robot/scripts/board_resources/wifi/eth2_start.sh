#!/bin/bash
sleep 5
/opt/robot/scripts/wifi/eth2_ctl.sh enable
sleep 1
/opt/robot/scripts/wifi/eth2_ctl.sh disable
sleep 1
/opt/robot/scripts/wifi/eth2_ctl.sh enable
sleep 5
# 循环检查 /sys/class/net/eth2 是否存在
while true; do
    if [ -d "/sys/class/net/eth2" ]; then
        echo "eth2 启动成功 "
	sleep 1
    else
	    /opt/robot/scripts/wifi/eth2_ctl.sh disable
	    sleep 1
	    echo "eth2 重启"
	    /opt/robot/scripts/wifi/eth2_ctl.sh enable
    fi
    sleep 5  # 等待一秒
done
