#!/bin/bash
set -e

# 参数处理：接口列表和可选的ping目标
NET_IFACES=()
PING_TARGETS=()
MODE="iface"  # 默认模式：只检查接口状态
TIMEOUT=60    # 接口检查超时时间（秒）
BROADCAST_TIMEOUT=5  # 广播测试超时时间（秒）

# 解析命令行参数
for arg in "$@"; do
    if [ "$arg" = "--ping" ]; then
        MODE="ping"
    elif [ "$MODE" = "iface" ]; then
        NET_IFACES+=("$arg")
    else
        PING_TARGETS+=($arg)
    fi
done

IFACES="${NET_IFACES[*]}"

echo "[wait_env] Interfaces to check: $IFACES"
if [ "${#PING_TARGETS[@]}" -gt 0 ]; then
    echo "[wait_env] Ping targets: ${PING_TARGETS[*]}"
fi

###############################################
# 检查网络接口
###############################################
for iface in "${NET_IFACES[@]}"; do
    # 先检查接口是否存在
    if ! ip link show "$iface" 2>/dev/null; then
        echo "[wait_env] WARNING: Interface $iface does not exist, skipping..."
        continue
    fi
    
    echo "[wait_env] Waiting for $iface UP..."
    timeout_counter=0
    until ip link show "$iface" 2>/dev/null | grep -q "state UP"; do
        sleep 1
        timeout_counter=$((timeout_counter + 1))
        if [ "$timeout_counter" -ge "$TIMEOUT" ]; then
            echo "[wait_env] WARNING: Timeout waiting for $iface to be UP, skipping..."
            continue 2  # 跳过当前接口的剩余检查
        fi
    done

    echo "[wait_env] Waiting for $iface IP..."
    timeout_counter=0
    until ip addr show "$iface" 2>/dev/null | grep -q "inet "; do
        sleep 1
        timeout_counter=$((timeout_counter + 1))
        if [ "$timeout_counter" -ge "$TIMEOUT" ]; then
            echo "[wait_env] WARNING: Timeout waiting for $iface IP, skipping..."
            continue 2  # 跳过当前接口的剩余检查
        fi
    done

    echo "[wait_env] $iface ready"
done

###############################################
# 可靠的 /dev/shm 检查
###############################################
echo "[wait_env] Checking /dev/shm mount..."

# 等待 /dev/shm 挂载完成
timeout_counter=0
until mount | grep -q "on /dev/shm type tmpfs"; do
    echo "[wait_env] /dev/shm not mounted yet, waiting..."
    sleep 1
    timeout_counter=$((timeout_counter + 1))
    if [ "$timeout_counter" -ge "$TIMEOUT" ]; then
        echo "[wait_env] ERROR: Timeout waiting for /dev/shm mount!"
        exit 1
    fi
done

# 再次测试可写性
if ! touch /dev/shm/test_$$ ; then
    echo "[wait_env] ERROR: /dev/shm not writable!"
    exit 1
fi
rm -f /dev/shm/test_$$

echo "[wait_env] /dev/shm OK"

############################################### 
# 新增：检查网络连通性 
############################################### 
if [ "${#PING_TARGETS[@]}" -gt 0 ]; then 
    for target in "${PING_TARGETS[@]}"; do 
        echo "[wait_env] Testing connectivity to $target..." 

        timeout=15
        count=0
        until ping -b -c 1 -W 1 "$target" >/dev/null 2>&1 || [ $count -ge $timeout ]; do 
            echo "[wait_env] Waiting for connectivity to $target... ($count/$timeout)" 
            count=$((count + 1))
            sleep 1
        done 
        
        # 检查是否成功连接 
        if [ $count -lt $timeout ]; then 
            echo "[wait_env] Connectivity to $target established" 
        else 
            echo "[wait_env] Failed to connect to $target within $timeout seconds" 
            # 可以选择在这里添加失败处理逻辑，比如退出脚本 
            # exit 1 
        fi 
    done 
fi

# wait ptp sync, date more than 2024
timeout_counter=0
current_year=$(date +%Y)
until [ "$current_year" -gt 2024 ]; do
    echo "[wait_env] Waiting for PTP sync... ($timeout_counter/$TIMEOUT)"
    sleep 1
    timeout_counter=$((timeout_counter + 1))
    if [ "$timeout_counter" -ge "$TIMEOUT" ]; then
        echo "[wait_env] ERROR: Timeout waiting for PTP sync!"
        exit 1
    fi
    current_year=$(date +%Y)  # 重新获取当前年份
done

echo "[wait_env] All checks passed!"
exit 0  # 明确返回成功状态