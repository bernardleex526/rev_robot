#!/bin/bash

cd /opt/robot/share/basic_server/bin

# ulimit -c unlimited

# sudo bash -c "echo '/var/opt/robot/log/system/coredump.%e.%p.%t' > /proc/sys/kernel/core_pattern"


taskset -c 1,2,3 chrt  60 ./basic_server