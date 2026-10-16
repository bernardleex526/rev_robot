#!/bin/bash

cd /opt/robot/share/node_driver/bin
taskset -c 6,7 chrt  45 ./rslidar