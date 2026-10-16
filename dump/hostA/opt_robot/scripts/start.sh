#!/bin/bash
/opt/robot/scripts/system/ldconfig.sh &
sleep 3
/opt/robot/scripts/board_resources/wifi/host_start.sh &
/opt/robot/scripts/board_resources/rtsp_service/start_server.sh &
#while true; do
/opt/robot/scripts/board_resources/storage_space/delete_log_file.sh &
/opt/robot/scripts/board_resources/storage_space/delete_record_file.sh &
#	sleep 84600
#done
