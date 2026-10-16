#!/bin/bash
os_type=$(cat /opt/robot/os_type)


while true; do

if [ -f /opt/robot/os_type ]; then
    if [ "$os_type" = "CA9B_VOS" ]; then
	if ! ip -4 addr show eth1 | grep -q "inet "; then
	    sudo ip addr add 10.21.31.105/24 dev eth1
	fi
    fi
    if [ "$os_type" = "CA9B_GOS" ]; then
	if ! ip -4 addr show eth0 | grep -q "inet "; then
	    sudo ip addr add 10.21.31.104/24 dev eth0
	fi
    fi
    if [ "$os_type" = "CA9B_NOS" ]; then
        echo "os_type=$os_type, 脚本直接退出"
	sleep 5
	if ! ip -4 addr show eth1 | grep -q "inet "; then
	    sudo ip addr add 10.21.31.106/24 dev eth1
	fi
    fi
    if [ "$os_type" = "CA9B_AOS" ]; then
        if ! ip -4 addr show eth2 | grep -q "inet "; then
  	    sudo ip addr add 10.21.31.103/24 dev eth2
            sudo ip addr add 10.21.33.103/24 dev eth0
	fi
    fi
fi
sleep 10
done
