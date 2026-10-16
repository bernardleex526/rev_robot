#!/bin/bash
# 脚本名称: get_mac_address.sh
# 用途: 获取 wlan0 接口的 MAC 地址，去掉其中的冒号，并打印输出后四位字符

# 检查 wlan0 接口是否存在
if [ ! -d /sys/class/net/wlan0 ]; then
  echo "Error: wlan0 interface does not exist."
  exit 1
fi

# 从系统文件中读取 MAC 地址，并移除所有冒号
MAC_ADDRESS=$(cat /sys/class/net/wlan0/address | tr -d ':')

# 检查是否成功读取到 MAC 地址
if [ -z "$MAC_ADDRESS" ]; then
  echo "Error: Could not read the MAC address of wlan0."
  exit 1
fi

# 取出 MAC 地址的后四位字符
LAST_FOUR_CHARS=${MAC_ADDRESS: -4}

# 打印后四位字符
echo "$LAST_FOUR_CHARS"