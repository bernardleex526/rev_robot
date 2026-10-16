#!/bin/bash

sudo journalctl --vacuum-size=0 --unit=mapping.service

SCRIPT_PATH=$(dirname "$(readlink -f "$0")")

# 定义颜色代码
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
WHITE=$(tput setaf 7)
RESET=$(tput sgr0)

usage() {
    echo "用法：" 
    echo "  drmap mapping [-options]"
    echo "  开始建图。"
    echo "选项："
    echo "  -b               只建图，但不用于导航"
    # echo "  -c               在同一场景下继续建图"
    echo "  -h               显示帮助信息并退出"
    echo "  -i               使用室内模式建图（默认模式）"
    echo "  -n [name]        指定地图（场景）名称"
    echo "  -o               使用室外模式建图"
    echo "  -s               关闭rviz可视化"
}

# edit_pcd="false"
activate="true"    # 用于导航
mode="indoor"  # 建图模式，默认室内
enable_rviz="true"
map_name="map"      # 地图名称前缀
continue_mapping="false"  # 是否继续建图

while getopts :bchin:os opt
do
    case "$opt" in
        b) activate="false"
        ;;
        c) continue_mapping="true"
        ;;
        h)
        usage
        exit 0
        ;;
        i) mode="indoor"
        ;;
        n) map_name_tmp=$OPTARG
        if [[ $map_name_tmp =~ ^- ]] || [ ! $map_name_tmp ]
        then
            echo "${RED}[ERROR] -n 选项需指定地图（场景）名称参数${RESET}" >& 2
            usage
            exit 1
        fi
        map_name=$map_name_tmp
        ;;
        o) mode="outdoor"
        ;;
        s) enable_rviz="false"  # 关闭rviz
        ;;
        :)
        echo "${RED}[ERROR] -$OPTARG 选项需指定参数${RESET}" >& 2
        usage
        exit 1
        ;;
        \?) 
        echo "${RED}[ERROR] 未知选项 -$OPTARG${RESET}" >& 2
        usage
        exit 1
        ;;
        # *) echo "Unknown option: -$opt" ;;
    esac
done

# echo "${GREEN}开始建图${RESET}"
# echo "${GREEN} - 地图名称：${map_name}${RESET}"
# echo "${GREEN} - 建图模式：${mode}${RESET}"
# echo "${GREEN} - 激活地图用于导航：${activate}${RESET}"
# echo "${GREEN} - 启用rviz可视化：${enable_rviz}${RESET}"
# echo "${GREEN} - 继续建图：${continue_mapping}${RESET}"

source $SCRIPT_PATH/config.sh

# echo "----- Step 1: 关闭定位程序-----"
bash $SCRIPT_PATH/pre_program.sh

# echo "----- Step 2: 初始化地图存储文件夹 -----"

date_time=$(date +"%Y%m%d-%H%M%S")

if [ $continue_mapping = "false" ]  # 建一张新地图
then
    # 创建文件夹名（包含字符串、日期和时间）
    folder_name="${map_name}-${date_time}"
    directory="${MAPS_PATH}/${folder_name}"     # 新地图真实目录
    # 创建目录
    mkdir -p "${directory}/.sessions/"
    chmod 777 -R ${directory}

    ### 拓扑地图目录
    # 简单地设为nav_map0并创建软链接
    mkdir -p "${directory}/.nav_maps/nav_map_0"
    if [ -d "${directory}/.nav_maps/active" ]; then        # 存在active路径
        if [ -L "${directory}/.nav_maps/active" ]; then    # active是个软链接
            rm -rf ${directory}/.nav_maps/active
        else
            mv ${directory}/.nav_maps/active ${directory}/.nav_maps/active-${date_time}   # 不是软链接，则备份一下
        fi
    else
        rm -rf ${directory}/.nav_maps/active
    fi
    ln -s ${directory}/.nav_maps/nav_map_0 ${directory}/.nav_maps/active
    ### 

    # 检查目录是否创建成功
    if [ ! -d "${directory}" ]; then
        echo "创建目录失败：${directory}"
        exit 1
    fi
    # 如果要激活地图
    if [ $activate = "true" ]; then
        # 检查是否存在maps/active文件夹
        if [ -d "$MAPS_PATH/active" ]; then        # 存在active路径
            if [ -L "$MAPS_PATH/active" ]; then    # active是个软链接
                rm -rf $MAPS_PATH/active
            else
                mv $MAPS_PATH/active $MAPS_PATH/active-${date_time}   # 不是软链接，则备份一下
            fi
        else
            rm -rf $MAPS_PATH/active
        fi
        ln -s ${directory} $MAPS_PATH/active     # active做为软链接，成为当前建图的工作目录
        # echo "创建并使用地图目录：${directory}"
        # 如果是ros1版本，则创建map软链接指向地图文件夹
        if [ $PROGRAM_VERSION = "noetic" ]; then
            # # 检查是否存在map文件夹
            # if [ -d "$MAPS_PATH/../map" ]; then        # 存在active路径
            #     if [ -L "$MAPS_PATH/../map" ]; then    # active是个软链接
            #         rm -rf $MAPS_PATH/../map
            #     else
            #         mv $MAPS_PATH/../map $MAPS_PATH/map-${date_time}   # 不是软链接，则备份一下
            #     fi
            # else
            #     rm -rf $MAPS_PATH/../map
            # fi
            rm -rf /home/ysc/jy_cog/system/map
            ln -s ${directory} /home/ysc/jy_cog/system/map     # active做为软链接，成为当前建图的工作目录
            chmod 777 -R /home/ysc/jy_cog/system/map
        fi
    fi

else
    # 找到软链接指向的真实目录
    if [ -d "$MAPS_PATH/active" ]; then  
        if [ -L "${MAPS_PATH}/active" ]; then       # 是个软链接
            directory=$(readlink "${MAPS_PATH}/active")
            # echo "继续建图，使用当前地图目录：${directory}"
        else        # 不是软链接
            mv $MAPS_PATH/active $MAPS_PATH/active-${date_time}   # 不是软链接，则备份一下
            directory=$MAPS_PATH/active-${date_time}
            # echo "继续建图，使用备份地图目录：${directory}"
        fi
    else
        # echo "选择了继续建图，但当前没有被激活的地图"
        rm -rf $MAPS_PATH/active
        exit 1
    fi
fi

echo "${GREEN}成功创建地图存储路径(map file path)：${directory}${RESET}"
# SCRIPT_PATH=$(dirname "$(readlink -f "$0")")
# echo "脚本路径：$SCRIPT_PATH"
# 如果需要使用rviz
if [ $enable_rviz = "true" ]; then
    echo "${GREEN}启用rviz可视化${RESET}"
    # 判断程序版本是noetic还是dds
    if [ $PROGRAM_VERSION = "dds" ]; then
        source /opt/ros/foxy/setup.bash
        export XAUTHORITY=/home/user/.Xauthority
        rviz2 -d ${SCRIPT_PATH}/../conf/slam.rviz >/dev/null 2>&1 &
    elif [ "$PROGRAM_VERSION" = "noetic" ]; then
        source /opt/ros/noetic/setup.bash
        rviz -d ${SCRIPT_PATH}/../conf/slam.rviz  >/dev/null 2>&1 &
    else
        echo "${RED}[ERROR] 未知的ROS版本参数：${PROGRAM_VERSION}${RESET}"
    fi
fi
# sudo chrt 49 taskset -c 4,5,6,7 $SCRIPT_PATH/../bin/lio_ddsnode ${directory} $mode
# 以service方式启动
# sudo systemctl start mapping.service
echo "${GREEN}开始执行建图程序. Start mapping program.${RESET}"
# sudo systemd-run --unit=mapping $SCRIPT_PATH/../bin/slam_ddsnode ${directory} $mode >/dev/null 2>&1
# CPUAffinity=4,5,6,7
if [ $PROGRAM_VERSION = "dds" ]; then
    sudo systemd-run --unit=mapping $SCRIPT_PATH/start_dds.sh ${directory} $mode # >/dev/null 2>&1
elif [ "$PROGRAM_VERSION" = "noetic" ]; then
    sudo systemd-run --unit=mapping $SCRIPT_PATH/start_ros1.sh ${directory} $mode # >/dev/null 2>&1
else
    echo "${RED}[ERROR] 未知的程序版本参数：${PROGRAM_VERSION}${RESET}"
fi

# 启动过程中额外运行脚本
bash $SCRIPT_PATH/extra.sh ${directory}

# 打印日志
# sudo journalctl -u mapping.service -f &