#!/bin/bash
execute_names=("localization_rosnode" "localization_ddsnode" "map_server")

for execute_name in ${execute_names[*]}
do
    echo "kill ${execute_name}"
    ps aux | grep -e ${execute_name} | grep -v grep | awk '{print $2}' | xargs -i kill -SIGINT {}
    while pgrep "${execute_name}" > /dev/null; do
        sleep 1
    done
done