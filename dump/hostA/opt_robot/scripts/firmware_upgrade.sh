#!/bin/bash
set -e
sleep 10
ECAN_FILE_DIR="/opt/robot/share/ecan_master/bin/"
JSON_FILE="/var/opt/robot/release_note.json"
SERVICE_NAME="firmware-upgrade"

ecan_file=("$ECAN_FILE_DIR"*.bin)
mcu_file=("$MCU_FILE_DIR"*.bin)
LOG_FILE="/var/opt/robot/log/ota.log"

log() {
  echo "[`date '+%Y-%m-%d %H:%M:%S'`] $1"
}

log "==== 固件升级脚本启动 ====" | tee -a "$LOG_FILE"



# -----------------------------
# 1️⃣ 检查 JSON 状态
# -----------------------------
if [ ! -f "$JSON_FILE" ]; then
    log "错误: JSON 文件不存在: $JSON_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 从 JSON 中读取字段值
DEB_STATUS=$(grep -Po '"DEB_UPGRADE_STATUS"\s*:\s*\K[0-9]+' "$JSON_FILE" || echo "")
FW_STATUS=$(grep -Po '"FIRMWARE_UPGRADE_STATUS"\s*:\s*\K[0-9]+' "$JSON_FILE" || echo "")

log "检测状态: DEB_UPGRADE_STATUS=$DEB_STATUS, FIRMWARE_UPGRADE_STATUS=$FW_STATUS" | tee -a "$LOG_FILE"

# 条件判断
if [[ "$DEB_STATUS" != "1" || "$FW_STATUS" != "0" ]]; then
    log "条件未满足，跳过固件升级" | tee -a "$LOG_FILE"
    exit 0
fi

# -----------------------------
# 2️⃣ 执行 ECAN 固件升级
# -----------------------------
ecan_file=("${ECAN_FILE_DIR}"*.bin)
if [ ! -d "$ECAN_FILE_DIR" ] || [ ! -e "${ecan_file[0]}" ]; then
    log "固件目录或文件不存在: $ECAN_FILE_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

# 捕获命令输出到变量
output=$(sudo /opt/robot/bin/FirmwareAssistant "${ecan_file[@]}" 2>&1)
# 显示输出
log "固件升级输出：" | tee -a "$LOG_FILE"
log "$output" | tee -a "$LOG_FILE"
# 检查执行结果
if [ $? -eq 0 ]; then
    log "固件升级成功" | tee -a "$LOG_FILE"
else
    log "固件升级失败" | tee -a "$LOG_FILE"
fi

ecan_git_commit_output=$(sudo /opt/robot/bin/FirmwareAssistant -v 2>/dev/null | grep "ECAN Git Commit ID" || true)
ecan_version_cmd=$(echo "$ecan_git_commit_output" | sed -n 's/.*ECAN Git Commit ID: \(V[0-9][0-9.]*\).*/\1/p')

if [ -n "$ecan_version_cmd" ]; then
    log "成功获取版本号: $ecan_version_cmd"
else
    log "错误: 未能提取版本号"
    exit 1
fi
log "检测到 ECAN Program Version: $ecan_version_cmd" | tee -a "$LOG_FILE"
if [ ! -f "$JSON_FILE" ]; then
    log "错误: JSON 文件不存在: $JSON_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

# 从 JSON 文件中读取 ECAN 字段
if [ ! -f "$JSON_FILE" ]; then
    log "错误: JSON 文件不存在: $JSON_FILE" | tee -a "$LOG_FILE"
    exit 1
fi

ecan_version_json=$(jq -r '.ECAN' "$JSON_FILE" 2>/dev/null)

if [ -z "$ecan_version_json" ] || [ "$ecan_version_json" = "null" ]; then
    log "错误: JSON 文件中未找到 ECAN 字段" | tee -a "$LOG_FILE"
    exit 1
fi

log "JSON 文件中记录的 ECAN 版本: $ecan_version_json" | tee -a "$LOG_FILE"

# 对比版本号是否一致
if [ "$ecan_version_json" = "$ecan_version_cmd" ]; then
    log "✅ 版本一致: $ecan_version_json" | tee -a "$LOG_FILE"
else
    log "❌ 版本不一致: 命令版本=$ecan_version_cmd, JSON版本=$ecan_version_json" | tee -a "$LOG_FILE"
    exit 1
fi

# -----------------------------
# 3️⃣ 修改 JSON 标志位
# -----------------------------
sudo sed -i -E \
    -e 's/"FIRMWARE_UPGRADE_STATUS"[[:space:]]*:[[:space:]]*0/"FIRMWARE_UPGRADE_STATUS": 1/g' \
    "$JSON_FILE" && \
    log "JSON 状态更新成功" | tee -a "$LOG_FILE"

log "==== 固件升级流程完成 ====" | tee -a "$LOG_FILE"

exit 0

