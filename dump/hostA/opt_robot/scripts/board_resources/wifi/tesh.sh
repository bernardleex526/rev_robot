#!/bin/bash
# 脚本名称: use_mac_address.sh
# 用途: 使用 get_mac_address.sh 的输出结果

# 调用第一个脚本并捕获其输出
FIRST_FOUR_CHARS=$(./get_mac_address.sh)

# 检查是否成功获取到 MAC 地址前四位
if [ -z "$FIRST_FOUR_CHARS" ]; then
  echo "Error: Could not obtain the MAC address from get_mac_address.sh."
  exit 1
fi

# 现在你可以使用 $FIRST_FOUR_CHARS 变量
echo "The first four characters of the MAC address are: $FIRST_FOUR_CHARS"

# 你可以在这里继续使用这个变量做其他事情
