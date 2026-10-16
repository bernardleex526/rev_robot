#!/bin/bash
cd /opt/robot/share/rte_checker/bin
sleep 10
taskset -c 2,3 chrt 20 ./run 5 1
