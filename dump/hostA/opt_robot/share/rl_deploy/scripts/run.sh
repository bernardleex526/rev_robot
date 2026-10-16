#!/bin/bash
cd /opt/robot/share/rl_deploy/bin

 ulimit -c unlimited
 sudo bash -c "echo '/var/opt/robot/log/system/coredump.%e.%p.%t' > /proc/sys/kernel/core_pattern"

# chrt 90 taskset -c 4,5,6,7 ./rl_deploy
chrt 90 taskset -c 4,5 ./rl_deploy
