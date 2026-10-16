#!/bin/bash

# 定义颜色代码
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
WHITE=$(tput setaf 7)
RESET=$(tput sgr0)

count=0

count_flag=("|" "/" "-" "\\")
suggess_info=""



# 订阅ROS话题
rostopic echo /localization_status/detail | while read -r line; do
 
    
    data=$(echo "$line" | grep -oP 'data: \K\[.*?\]' | tr -d '[]')
    
    # 将数据分割成数组
    IFS=', ' read -r -a array <<< "$data"
    
    # 检查数组长度是否正确
    if [ ${#array[@]} -ne 15 ]; then
        # echo "Error: Array length is not 14, actual length is ${#array[@]}"
        continue
    fi
    
    # 清屏
    clear

    # 获取终端的宽度和高度
    cols=$(tput cols)
    rows=$(tput lines)

    # echo $data
    count=$((count + 1))
    if [ $count -gt 3 ]  
    then  
    count=0 
    fi
    
    # # 获取当前时间
    current_time=$(date "+%Y-%m-%d %H:%M:%S")
    
    # # 打印当前时间
    echo "[${count_flag[count]}] $current_time"


    for ((i=1; i<=$(( cols / 3 )); i++))  
    do  
        echo -n "-  "  
    done
    printf "\n"
    

    # 打印总体状态
    elem="${array[0]}"
    elem_width=$cols
    case $elem in
        0) 
        color=$GREEN 
        info="正常"
        ;;
        1) 
        color=$BLUE 
        info="初始化"
        ;;
        2) 
        color=$YELLOW 
        info="异常"
        suggess_info="$suggess_info${color}[WARN ]关注详细异常${RESET}\n"
        ;;
        3) 
        color=$RED 
        info="丢失，尝试重定位"
        suggess_info="$suggess_info${color}[ERROR]建议等待${RESET}\n"
        ;;
        4) 
        color=$RED 
        info="丢失"
        suggess_info="$suggess_info${color}[ERROR]建议排查其它模块问题${RESET}\n"
        ;;
        5) 
        color=$RED 
        info="丢失"
        suggess_info="$suggess_info${color}[ERROR]建议重新给定初始位姿${RESET}\n"
        ;;
        6) 
        color=$RED 
        info="丢失"
        suggess_info="$suggess_info${color}[ERROR]建议重启定位程序${RESET}\n"
        ;;
        *) 
        color=$RED 
        info="未知"
        ;;
    esac
    
    # 打印元素标签和值，根据元素宽度进行格式化
    msg="总体状态：${color}${info}${RESET}"
    # 计算msg的长度
    msg_length=${#msg}
    # 计算前后需要填充的空格数以达到居中
    padding=$(( (elem_width - msg_length) / 2 ))
    printf "%${padding}s%s\n" "" "$msg"


    # 打印传感器状态
    input_string=("雷达" "IMU" "里程计" "RTK" "标志" "反光条")
    input_length=(4 3 6 3 4 6)
    elem_width=$(( cols / 6 ))
    # printf "%-${cols}s" "-"
    for ((i=1; i<=$(( cols / 3 )); i++))  
    do  
        echo -n "-  "  
    done
    printf "\n"
    
    for i in {1..6}; do
        msg="${input_string[i-1]}"
        # 计算msg的长度
        msg_length=${#msg}
        msg_length=${input_length[i-1]}
        # echo "cols: $cols"
        # echo "msg_length: $msg_length"
        # echo "elem_width: $elem_width"
        # 计算前后需要填充的空格数以达到居中
        padding1=$(( (elem_width - msg_length) / 2 - 1))
        padding2=$(( (elem_width - msg_length - padding1 - 2)))
        # echo "padding1: $padding1"
        # echo "padding2: $padding2"
        
        printf "|%${padding1}s%s%${padding2}s|" "" "$msg" ""
    done
    printf "\n"
    for i in {1..6}; do
        elem="${array[$i]}"
        case $elem in
            0) 
            color=$GREEN 
            info="不使用"
            info_length=6
            ;;
            1) 
            color=$GREEN 
            info="正常"
            info_length=4
            ;;
            2) 
            color=$RED 
            info="无数据"
            info_length=6
            suggess_info="$suggess_info${color}[ERROR]建议排查${input_string[i-1]}驱动及硬件${RESET}\n"
            ;;
            3) 
            color=$YELLOW 
            info="异常"
            info_length=4
            ;;
            *) 
            color=$RED 
            info="未知"
            info_length=4
            ;;
        esac
        
        # 打印元素标签和值，根据元素宽度进行格式化
        msg="${color}${info}${RESET}"
        # 计算msg的长度
        # msg_length=${#msg}
        # # 计算前后需要填充的空格数以达到居中
        # padding=$(( (elem_width - msg_length) / 2 - 2))
        # echo "padding: $padding"
        # echo "elem_width: $elem_width"
        # echo "msg_length: $msg_length"
        # printf "%${padding}s%s" " " "$msg"
        padding1=$(( (elem_width - info_length) / 2 - 1))
        padding2=$(( (elem_width - info_length - padding1 - 2))) 
        printf "|%${padding1}s%s%${padding2}s|" "" "$msg" ""
    done
    
    printf "\n"

    # 打印丢失状态
    input_string=("IMU误差" "里程计误差" "匹配误差" "发布时间")
    suggess_input=("查看RVIZ上定位位置与实际是否相符；关注狗实际运动是否有打滑或不稳" "查看RVIZ上定位位置与实际是否相符；关注狗实际运动是否有打滑或不稳" "查看RVIZ上定位位置与实际是否相符；检查当前位置是否在已建图区域" "检查传感器状态；关注是否有计算超时")
    input_length=(7 10 8 8)
    elem_width=$(( cols / 4 ))
    # printf "%-${cols}s" "-"
    for ((i=1; i<=$(( cols / 3 )); i++))  
    do  
        echo -n "-  "  
    done
    printf "\n"
    
    for i in {0..3}; do
        msg="${input_string[i]}"
        # 计算msg的长度
        msg_length=${#msg}
        msg_length=${input_length[i]}
        # 计算前后需要填充的空格数以达到居中
        padding1=$(( (elem_width - msg_length) / 2 - 1))
        padding2=$(( (elem_width - msg_length - padding1 - 2)))   
        printf "|%${padding1}s%s%${padding2}s|" "" "$msg" ""
    done
    printf "\n"
    for i in {7..10}; do
        elem="${array[$i]}"
        case $elem in
            0) 
            color=$GREEN 
            info="正常"
            info_length=4
            ;;
            1) 
            color=$YELLOW 
            info="警告"
            info_length=4
            suggess_info="$suggess_info${color}[WARN ]${suggess_input[i-7]}${RESET}\n"
            ;;
            2) 
            color=$RED 
            info="丢失"
            info_length=4
            suggess_info="$suggess_info${color}[ERROR]${suggess_input[i-7]}${RESET}\n"
            ;;
            *) 
            color=$RED 
            info="未知"
            info_length=4
            ;;
        esac
        
        # 打印元素标签和值，根据元素宽度进行格式化
        msg="${color}${info}${RESET}"
        padding1=$(( (elem_width - info_length) / 2 - 1))
        padding2=$(( (elem_width - info_length - padding1 - 2))) 
        printf "|%${padding1}s%s%${padding2}s|" "" "$msg" ""
    done

    printf "\n"

    # 打印其它状态
    input_string=("超时异常" "数值异常" "时间戳异常")
    suggess_input=("检查htop资源占用；关闭RVIZ等不必要的程序" "关注程序是否正常运行，必要时重启程序" "检查是否有对时程序导致系统时间跳变")
    input_length=(8 8 10)
    elem_width=$(( cols / 3 ))
    # printf "%-${cols}s" "-"
    for ((i=1; i<=$(( cols / 3 )); i++))  
    do  
        echo -n "-  "  
    done
    printf "\n"
    
    for i in {0..2}; do
        msg="${input_string[i]}"
        # 计算msg的长度
        msg_length=${#msg}
        msg_length=${input_length[i]}
        # 计算前后需要填充的空格数以达到居中
        padding1=$(( (elem_width - msg_length) / 2 - 1))
        padding2=$(( (elem_width - msg_length - padding1 - 2)))   
        printf "|%${padding1}s%s%${padding2}s|" "" "$msg" ""
    done
    printf "\n"
    for i in {11..13}; do
        elem="${array[$i]}"
        case $elem in
            0) 
            color=$GREEN 
            info="正常"
            info_length=4
            ;;
            1) 
            color=$YELLOW 
            info="异常"
            info_length=4
            suggess_info="$suggess_info${color}[ERROR]${suggess_input[i-11]}${RESET}\n"
            ;;
            *) 
            color=$RED 
            info="未知"
            info_length=4
            ;;
        esac
        
        # 打印元素标签和值，根据元素宽度进行格式化
        msg="${color}${info}${RESET}"
        padding1=$(( (elem_width - info_length) / 2 - 1))
        padding2=$(( (elem_width - info_length - padding1 - 2))) 
        printf "|%${padding1}s%s%${padding2}s|" "" "$msg" ""
    done

    printf "\n"

    for ((i=1; i<=$(( cols / 3 )); i++))  
    do  
        echo -n "-  "  
    done
    printf "\n处理建议：\n"
    # printf "%s" "$suggess_info"
    echo -e $suggess_info
    suggess_info=""
done