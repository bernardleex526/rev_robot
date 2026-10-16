#!/bin/bash
# 建图结束前执行内容
SCRIPT_PATH=$(dirname "$(readlink -f "$0")")

sudo systemctl stop keyframe_saver.service >/dev/null 2>&1
sudo systemctl reset-failed keyframe_saver.service >/dev/null 2>&1