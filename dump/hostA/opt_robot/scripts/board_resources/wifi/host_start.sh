#!/bin/bash
/opt/robot/scripts/board_resources/start_ctrl/start_ctrl.sh &

if [ -f /opt/robot/os_type ]; then
    os_type=$(cat /opt/robot/os_type)
    if [ "$os_type" = "CA9B_VOS" ]; then
        echo "os_type=$os_type, 脚本直接退出"
	/opt/robot/scripts/wifi/ptp106.sh &
	sleep 10
	cd /etc/netplan/
	ip addr show eth1 | grep -w inet |  grep -w 10.21.31.105
        if [ $? -ne 0 ]
        then
                echo "eth0 ip is not 10.21.31.105, exec netplan apply"
                netplan apply
                sleep 10
        fi
	sleep 10
	/opt/robot/scripts/wifi/ip_set.sh &
        exit 1
    fi
    if [ "$os_type" = "CA9B_GOS" ]; then
        echo "os_type=$os_type, 脚本直接退出"
	/opt/robot/scripts/wifi/ptp104.sh &
	sleep 10
	cd /etc/netplan/
	ip addr show eth0 | grep -w inet |  grep -w 10.21.31.104
        if [ $? -ne 0 ]
        then
                echo "eth0 ip is not 10.21.31.104, exec netplan apply"
                netplan apply
                sleep 10
        fi
	sleep 10
	/opt/robot/scripts/wifi/ip_set.sh &
        exit 1
    fi
    if [ "$os_type" = "CA9B_NOS" ]; then
        echo "os_type=$os_type, 脚本直接退出"
	/opt/robot/scripts/wifi/ptp106.sh &
	sleep 10
	cd /etc/netplan/
	ip addr show eth1 | grep -w inet |  grep -w 10.21.31.106
	if [ $? -ne 0 ]
	then
    		echo "eth0 ip is not 10.21.31.106, exec netplan apply"
    		netplan apply
        	sleep 10
	fi
	sleep 10
	/opt/robot/scripts/wifi/ip_set.sh &
	exit 1
    fi
fi
/opt/robot/scripts/wifi/ptp103.sh &
/opt/robot/scripts/wifi/wifi_start.sh  &
/opt/robot/scripts/wifi/eth2_start.sh  &
sleep 5

/opt/robot/scripts/wifi/ap_start.sh start 24G > /var/opt/robot/log/ap.log

sleep 10
cd /etc/netplan/

#check eth0 ip if not 10.21.33.103, exec netplan apply
ip addr show eth0 | grep -w inet |  grep -w 10.21.33.103
if [ $? -ne 0 ]
then
    echo "eth0 ip is not 10.21.33.103, exec netplan apply"
    netplan apply
	sleep 10
fi

/opt/robot/scripts/wifi/ip_set.sh &


/opt/robot/scripts/wifi/loop_start_ap.sh
