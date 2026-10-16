#!/bin/bash
DATA_PATH=${1:-"/home/ysc/jy_cog/system/record/localization_data"}
# 固定前缀
PREFIX="error_data"
# 保留的最大天数
DAYS_TO_KEEP=15
MAX_AGE=$((DAYS_TO_KEEP * 24 * 60 * 60))

# 创建当前日期时间的文件夹
TIMESTAMPSECOND=$(date +%s)
TIMESTAMP=$(date -d "@${TIMESTAMPSECOND}" +"%Y%m%d_%H%M%S")
NEW_DIR="$DATA_PATH/${TIMESTAMP}_${PREFIX}_${TIMESTAMPSECOND}"

mkdir -p "$NEW_DIR"
echo "Created directory: $NEW_DIR"

# 创建软链接，重新链接到新创建的文件夹
if [ -L "$DATA_PATH/${PREFIX}" ]; then
    rm "$DATA_PATH/${PREFIX}"  # 删除旧的软链接
fi
ln -s "$NEW_DIR" "$DATA_PATH/${PREFIX}"
# echo "Updated symlink: ${PREFIX} -> $NEW_DIR"

# 删除指定时间前的文件夹
for dir in $DATA_PATH/*_${PREFIX}_*; do
    if [[ -d "$dir" ]]; then
        # 提取时间后缀并转换为时间戳
        TIMESTAMP_STR="${dir#*${PREFIX}_}"
        #DIR_TIMESTAMP=$(date -d "${TIMESTAMP_STR}" +%s 2>/dev/null)
        #echo "Allfolder: $dir"

        #echo "TIMESTAMPSECOND: $TIMESTAMPSECOND"
        # echo "TIMESTAMP_STR: $TIMESTAMP_STR"

        if [[ $? -eq 0 && $((TIMESTAMPSECOND - TIMESTAMP_STR)) -gt MAX_AGE ]]; then
            rm -rf "$dir"
            echo "Deleted data folder: $dir"
        fi
    fi
done