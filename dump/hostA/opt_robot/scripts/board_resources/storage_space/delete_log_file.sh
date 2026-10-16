#!/usr/bin/env bash
# 清理脚本：当分区使用率 > 80 % 时，删最旧文件直到 <= 50 %
# -----------------------------

bash /opt/robot/scripts/board_resources/storage_space/delete_log_record.sh  &
bash /opt/robot/scripts/board_resources/storage_space/delete_log_robot.sh  &
bash /opt/robot/scripts/board_resources/storage_space/delete_log_sys.sh  &
