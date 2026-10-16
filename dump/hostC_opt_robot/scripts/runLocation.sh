#!/bin/bash

cd /opt/robot/share/charge_manager/bin

taskset -c 4,5 chrt 50 ./reflective_column_node