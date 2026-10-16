#!/usr/bin/env bash
# 清理脚本：当分区使用率 > 80 % 时，删最旧文件直到 <= 50 %
# -----------------------------
set -euo pipefail

MOUNTPOINT="/var/log/"          # 目标挂载点——改成自己的
HIGH_LIMIT=70               # 触发清理阈值
LOW_LIMIT=50                # 清理结束阈值
LOGFILE="/var/log/partition_clean_sys.log"

while true; do
{
# 取分区使用率（整数，去掉%）
usage_pct() {
   df -P "$MOUNTPOINT" | awk 'NR==2 {sub(/%/,"",$5); print $5}'
}

echo "=== $(date '+%F %T') 开始检查 $MOUNTPOINT ===" >> $LOGFILE
current=$(usage_pct)
echo "当前使用率: ${current}%" >> $LOGFILE

if (( current < HIGH_LIMIT )); then
    echo "未超过 ${HIGH_LIMIT}%，无需清理。" >> $LOGFILE
else
{
echo "使用率 > ${HIGH_LIMIT}%，开始删除旧文件……" >> $LOGFILE
# 列出分区内所有普通文件，按 mtime 升序（最旧在前）
# %T@ = Unix 时间戳，空格分隔后第二列是完整路径
find "$MOUNTPOINT" -xdev -type f -printf '%T@ %p\n' \
    | sort -n |
    while read -r ts filepath; do
        # 可在这里加白名单排除条件，例如：
        # [[ "$filepath" == */important/* ]] && continue
        rm -f -- "$filepath" && echo "删 $filepath" >> $LOGFILE
        current=$(usage_pct)
        if (( current <= LOW_LIMIT )); then
            echo "已降到 ${current}% <= ${LOW_LIMIT}% —— 停止。"  >> $LOGFILE
            break
        fi
    done

echo "结束后使用率: $(usage_pct)%" >> $LOGFILE
echo "=== 结束 ===" >> $LOGFILE
}
fi
sleep 300
}
done
