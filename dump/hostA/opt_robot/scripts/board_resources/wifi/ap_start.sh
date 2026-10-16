#!/bin/bash  

# con-name 
CC_NAME_24G=myap24G
CC_NAME_5G=myap50G
sudo nmcli connection delete myap50G
dhcpip=10.21.41.1/24
SSID_PSK=12345678
# 5G channel 36 40 44 48 52~64 100~104  149~165
channel=40
apdevice=""

if [ -d /sys/class/net/wlan0 ];then
    apdevice=wlan0
fi

if [ -d /sys/class/net/wlan0 ];then
    apdevice=wlan0
fi
if [ $apdevice == "" ];then
    echo "no wifi device"
    exit 0
fi

HOST_NAME_FILEPATH="/var/opt/robot/conf/host_name"
if [ ! -s "$HOST_NAME_FILEPATH" ]; then
    echo CA9B_NO0_5G > $HOST_NAME_FILEPATH
else
    host_name=$(head -c 12 $HOST_NAME_FILEPATH)
fi

if [ ! -s "$HOST_NAME_FILEPATH" ]; then
    host_name="CA9B_NO0_5G"
fi

HOST_NAME_FILEPATH="/opt/robot/scripts/wifi/password"
password=$(head -c 16 $HOST_NAME_FILEPATH)
if [ -z "$password" ]; then
	echo "password if empty using default"
    echo $SSID_PSK > $HOST_NAME_FILEPATH
else
	SSID_PSK=$password
fi

if [ -z "$host_name" ]; then
	echo "host_name is empty using default"
else
	SSID_24G="$host_name"_24G
	SSID_50G="$host_name"_5G
fi

function create_ap_5G()
{
    nmcli radio wifi on
    iw reg set CN
    nmcli c add type wifi ifname $apdevice con-name $CC_NAME_5G autoconnect no ssid $SSID_50G
    nmcli c modify $CC_NAME_5G 802-11-wireless.mode ap 802-11-wireless.band a 802-11-wireless.channel $channel 802-11-wireless.powersave 2 ipv4.method shared
    nmcli c modify $CC_NAME_5G 802-11-wireless-security.key-mgmt wpa-psk
    nmcli c modify $CC_NAME_5G 802-11-wireless-security.psk $SSID_PSK
    nmcli con modify $CC_NAME_5G ipv4.addresses $dhcpip
    nmcli connection up $CC_NAME_5G
    sudo sysctl -w net.ipv4.ip_forward=1
}

function create_ap_24G()
{
    nmcli radio wifi on
    iw reg set CN
    nmcli c add type wifi ifname $apdevice con-name $CC_NAME_24G autoconnect no ssid $SSID_24G
    nmcli connection modify $CC_NAME_24G 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
    nmcli connection modify $CC_NAME_24G wifi-sec.key-mgmt wpa-psk
    nmcli connection modify $CC_NAME_24G wifi-sec.psk $SSID_PSK
    nmcli con modify  $CC_NAME_24G ipv4.addresses $dhcpip
    nmcli connection up $CC_NAME_24G
    sudo sysctl -w net.ipv4.ip_forward=1
}

function close_ap()
{
    echo "try to close ap " 
    ret=$(nmcli c show | grep myap | awk 'NR=='1' {print$1}')
    if [ -z "$ret" ];then
        echo "no ap "
        return 0
    fi
    echo "current ap connection is $ret"
    if [ "$CC_NAME_24G" == "$ret" ] || [ "$CC_NAME_5G" == "$ret" ];then
        nmcli c delete $ret
        echo "delete ap success"
    fi
}

usage()
{
	echo "USAGE: "
	echo "./ap_start.sh start 5G    Create a 5G ap use default SSID and password"
    echo "./ap_start.sh start 24G   Create a 2.4G ap use default SSID and password"
    echo "./ap_start.sh stop        Close the created ap "
    exit 1
}

case $1 in 
    start)
        echo "start $2 ap"
        close_ap
        if [ -z $2 ];then 
            usage
        fi
        if [ $2 == "5G" ];then
            create_ap_5G
        fi
        if [ $2 == "24G" ];then
            create_ap_24G
        fi
        ;;
    stop)
        close_ap
        ;;
    *)
        usage
        ;;
esac

