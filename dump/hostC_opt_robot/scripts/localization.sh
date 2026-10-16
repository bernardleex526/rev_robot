#!/bin/bash

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
# echo "脚本路径: "
# echo $SCRIPT_PATH
bash $SCRIPT_PATH/localization_stop.sh
sleep 1s
export LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib/x86_64-linux-gnu:/opt/robot/share/localization/lib:$LD_LIBRARY_PATH


# 检查 version 文件是否存在且内容是否为 2.0
# if [ ! -f "/home/ysc/jy_cog/system/map/loc_map/version" ] || [ "$(cat "/home/ysc/jy_cog/system/map/loc_map/version")" != "2.0" ]; then
#     echo "地图版本不一致，重新生成地图"

#     # 删除目标文件夹（如果存在）
#     if [ -d "/home/ysc/jy_cog/system/map/loc_map" ]; then
#         echo "删除原始地图文件夹"
#         rm -rf "/home/ysc/jy_cog/system/map/loc_map"
#     fi

#     # 创建目标文件夹
#     echo "重新创建地图文件夹"
#     mkdir "/home/ysc/jy_cog/system/map/loc_map"

#     # 更新 version 文件，确保其内容为 2.0
#     echo "2.0" > "/home/ysc/jy_cog/system/map/loc_map/version"
#     echo "更新 version 文件内容为 2.0"
# else
#     echo "地图版本正确"
# fi



bash $SCRIPT_PATH/manage_data.sh "/home/ysc/jy_cog/system/record/localization_data"
sleep 1s

echo "启动ros1节点"
source $SCRIPT_PATH/../setup.bash
# sudo chrt 50 taskset -c 4,5 $SCRIPT_PATH/../bin/localization_rosnode
$SCRIPT_PATH/../bin/map_server "/home/ysc/jy_cog/system/map/jueying.yaml" &
$SCRIPT_PATH/../bin/localization_rosnode