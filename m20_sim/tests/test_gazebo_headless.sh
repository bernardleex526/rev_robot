#!/bin/bash
# Headless Gazebo end-to-end test: spawn M20, start patched rl_deploy, stand -> RL -> walk, track ground truth.
W=${W:-~/m20_sim_ws}
source "$W/env.sh"
export ROS_DOMAIN_ID=41
pkill -f gzserver 2>/dev/null; pkill -f rl_deploy 2>/dev/null; sleep 1
LOG=/tmp/m20_gz; mkdir -p $LOG
timeout 150 ros2 launch m20_gazebo m20_gazebo.launch.py gui:=false rl_deploy:=true > $LOG/launch.log 2>&1 &
for i in $(seq 1 90); do ros2 topic list 2>/dev/null | grep -q /JOINTS_DATA && grep -q 'listening on /sim_cmd' $LOG/launch.log && break; sleep 1; done
echo "ready after ${i}s"
sleep 2
echo "--- topics / rates"
ros2 topic list | grep -E 'JOINTS|IMU|sim_'
timeout 5 ros2 topic hz /JOINTS_DATA 2>&1 | grep average | tail -1
timeout 5 ros2 topic hz /JOINTS_CMD 2>&1 | grep average | tail -1
echo "--- RTF"; timeout 4 gz stats -p 2>/dev/null | tail -2 | awk -F, '{print "real_time_factor="$1}'
echo "--- initial"; ros2 run m20_gazebo base_pose.py; ros2 run m20_gazebo m20_cmd.py status
ros2 run m20_gazebo m20_cmd.py stand; sleep 6
echo "--- after stand"; ros2 run m20_gazebo base_pose.py
ros2 run m20_gazebo m20_cmd.py rl; sleep 3
echo "--- after rl"; ros2 run m20_gazebo base_pose.py; ros2 run m20_gazebo m20_cmd.py status
ros2 run m20_gazebo m20_cmd.py vel 0.6 0 0 5
echo "--- after walk 5s"; ros2 run m20_gazebo base_pose.py
ros2 run m20_gazebo m20_cmd.py vel 0 0 0.6 4
echo "--- after turn 4s"; ros2 run m20_gazebo base_pose.py
ros2 run m20_gazebo m20_cmd.py status
echo "--- launch log (errors)"; grep -iE 'error|fatal|exception|bridge loaded|Command source|target_mode' $LOG/launch.log | head -15
pkill -f gzserver; pkill -f rl_deploy; pkill -f robot_state_publisher
