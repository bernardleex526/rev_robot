#!/bin/bash
# A/B: does the MuJoCo RL divergence depend on scene or on the wrapper? Runs stand->rl->walk for each variant.
W=${W:-~/m20_sim_ws}
source "$W/env.sh"
run_case() {  # $1=label $2=domain $3...=sim command
  local label=$1 dom=$2; shift 2
  export ROS_DOMAIN_ID=$dom
  local L=/tmp/m20_ab_$label; mkdir -p $L
  pkill -f run_mujoco_bridge; pkill -f sim_headless; pkill -f rl_deploy; sleep 1
  ( cd "$M20_SDK_DIR/interface/robot/simulation" && timeout 60 "$@" > $L/sim.log 2>&1 & )
  sleep 4
  M20_CMD_SOURCE=ros timeout 55 stdbuf -oL ros2 run m20_sdk_deploy rl_deploy > $L/rl.log 2>&1 &
  for i in $(seq 1 40); do ros2 topic info /sim_mode 2>/dev/null | grep -q 'Subscription count: [1-9]' && break; sleep 1; done
  sleep 1
  ros2 run m20_gazebo m20_cmd.py stand >/dev/null; sleep 6
  ros2 run m20_gazebo m20_cmd.py rl >/dev/null; sleep 4
  ros2 run m20_gazebo m20_cmd.py vel 0.6 0 0 3 >/dev/null
  local st; st=$(ros2 run m20_gazebo m20_cmd.py status 2>&1 | tr '\n' ' ')
  local crash; crash=$(grep -c AssertionError $L/sim.log)
  echo "[$label] crash=$crash  $st" | cut -c1-200
  pkill -f run_mujoco_bridge; pkill -f sim_headless; pkill -f rl_deploy; sleep 1
}
SIMDIR="$M20_SDK_DIR/interface/robot/simulation"
sed 's/^USE_VIEWER = True/USE_VIEWER = False/' "$SIMDIR/mujoco_simulation_ros2.py" > "$SIMDIR/sim_headless.py"
run_case official_stair 51 python3 sim_headless.py
run_case wrapper_stair 52 ros2 run m20_gazebo run_mujoco_bridge.py --headless --scene stair
run_case wrapper_flat 53 ros2 run m20_gazebo run_mujoco_bridge.py --headless --scene flat
