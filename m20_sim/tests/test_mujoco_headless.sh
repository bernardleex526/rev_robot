#!/bin/bash
# Headless MuJoCo end-to-end test with the same patched rl_deploy and the same command tool as Gazebo.
# KNOWN ISSUE: with cross-process rl_deploy the robot tips over ~2 s after entering RL (reproduces with the
# unmodified official bridge, see ab_mujoco.sh). Use Gazebo for the ROS stack, mujoco/mujoco_inproc.py for MuJoCo.
W=${W:-~/m20_sim_ws}
source "$W/env.sh"
export ROS_DOMAIN_ID=42
pkill -f run_mujoco_bridge 2>/dev/null; pkill -f rl_deploy 2>/dev/null; sleep 1
LOG=/tmp/m20_mj; mkdir -p $LOG
timeout 150 ros2 run m20_gazebo run_mujoco_bridge.py --headless --scene flat > $LOG/sim.log 2>&1 &
sleep 4
M20_CMD_SOURCE=ros timeout 140 stdbuf -oL ros2 run m20_sdk_deploy rl_deploy > $LOG/rl.log 2>&1 &
for i in $(seq 1 60); do ros2 topic info /sim_mode 2>/dev/null | grep -q 'Subscription count: [1-9]' && break; sleep 1; done
echo "ready after ${i}s"; sleep 2
timeout 5 ros2 topic hz /JOINTS_DATA 2>&1 | grep average | tail -1
echo "--- initial"; ros2 run m20_gazebo base_pose.py; ros2 run m20_gazebo m20_cmd.py status
ros2 run m20_gazebo m20_cmd.py stand; sleep 6
echo "--- after stand"; ros2 run m20_gazebo base_pose.py
ros2 run m20_gazebo m20_cmd.py rl; sleep 3
echo "--- after rl"; ros2 run m20_gazebo base_pose.py
ros2 run m20_gazebo m20_cmd.py vel 0.6 0 0 5
echo "--- after walk 5s"; ros2 run m20_gazebo base_pose.py
ros2 run m20_gazebo m20_cmd.py vel 0 0 0.6 4
echo "--- after turn 4s"; ros2 run m20_gazebo base_pose.py
ros2 run m20_gazebo m20_cmd.py status
grep -iE 'scene=|real_time_factor|error|Traceback' $LOG/sim.log | head -12
pkill -f run_mujoco_bridge; pkill -f rl_deploy
