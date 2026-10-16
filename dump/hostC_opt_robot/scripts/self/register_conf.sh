#!/bin/bash
source_path=${1:-""}
target_path=${2:-""}
file_list=("params.yaml")

# 检查系统架构
ARCH=$(uname -m)
# install ruamel.yaml
echo "---- Installing ruamel.yaml ----"
if pip3 list | grep -F "ruamel" > /dev/null; then
    echo "ruamel is already installed."
else
    echo "ruamel is not installed. Installing..."
    case $ARCH in
        x86_64)
            echo "This is an x86_64 system."
            pip3 install $source_path/../scripts/self/lib/ruamel.yaml.clib-0.2.8-cp38-cp38-manylinux_2_5_x86_64.manylinux1_x86_64.whl
            pip3 install $source_path/../scripts/self/lib/ruamel.yaml-0.18.5-py3-none-any.whl
        ;;
        arm* | aarch64)
            echo "This is an ARM system. "
            pip3 install $source_path/../scripts/self/lib/ruamel.yaml.clib-0.2.7-cp38-cp38-manylinux2014_aarch64.whl
            pip3 install $source_path/../scripts/self/lib/ruamel.yaml-0.18.5-py3-none-any.whl
        ;;
        *)
            echo "Unknown architecture: $ARCH"
        ;;
    esac
    
fi

# time=$(date "+%Y%m%d%H%M%S")
for file_name in ${file_list[@]}
do
    echo "---- Registering $file_name config ----"
    
    # for file_path in $source_path/*         #遍历原始路径下所有文件
    # do
        # file_name=$(basename "$file_path")
        # echo "Find config file: $file_name" 
    if [ -e $source_path/$file_name ]; then
        echo "Find file: $file_name in $source_path" 
        if [ ! -e $target_path/$file_name ]; then     # 目标路径下不存在这个文件
            echo "$file_name does not exist in $target_path. Register it"
            mkdir -p $target_path && cp $source_path/$file_name "$_"
        else
            # mkdir -p $target_path/history       # 创建一个历史文件夹
            if [[ $file_name == *.yaml ]] || [[ $file_name == *.yml ]]; then    # 是yaml格式，进行更新
                echo "$file_name is a YAML file. Update params."
                # 先备份用户配置
                # cp $target_path/$file_name $target_path/history/$file_name.$time
                
                if [ ! $source_path = $target_path ]
                then
                    # 放置默认配置
                    cp $source_path/$file_name $target_path
                fi
                
                # case $ARCH in
                #     x86_64)
                        # 再用用户配置更新默认配置
                        if [ -e $target_path/$file_name.last ]; then
                            python3 $source_path/../scripts/self/update_yaml.py $target_path/$file_name.last $target_path/$file_name
                            echo "finish update user config"
                        fi
                        # 再更新需要强行更新的配置
                        if [ -e $source_path/$file_name.update ]; then
                            python3 $source_path/../scripts/self/update_yaml.py $source_path/$file_name.update $target_path/$file_name
                            echo "finish update necessary config"
                        fi
                #     ;;
                #     arm* | aarch64)
                #         echo "Please update the parameters manually."
                #     ;;
                #     *)
                #         echo "Please update the parameters manually."
                #     ;;
                # esac
            fi
        fi
    fi
    # done
done
# chmod -R 777 $target_path
