#!/bin/bash

cd /opt/robot/share/node_driver/bin
taskset -c 1,2,3 ./gps_node