#!/bin/bash
# Headless sim-to-sim smoke test: official SDK rl_deploy (x86) <-> MuJoCo bridge over DDS.
# Requires 01_build_drdds_and_sdk.sh and a python with mujoco+scipy (e.g. ~/.venvs/m20).
W=${W:-~/m20_ws}
VENV=${VENV:-~/.venvs/m20}
cd "$W"
source /opt/ros/humble/setup.bash
source install/setup.bash
[ -d "$W/.deps" ] && export LD_LIBRARY_PATH="$W/.deps/root/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-37}
export PYTHONPATH="$PYTHONPATH:$("$VENV/bin/python" -c 'import site;print(site.getsitepackages()[0])')"
SIMDIR=src/M20_sdk_deploy/interface/robot/simulation
sed 's/^USE_VIEWER = True/USE_VIEWER = False/' "$SIMDIR/mujoco_simulation_ros2.py" > "$SIMDIR/sim_headless.py"
(cd "$SIMDIR" && timeout 40 python3 sim_headless.py > /tmp/sim.log 2>&1 &)
sleep 3
(timeout 35 ros2 run m20_sdk_deploy rl_deploy > /tmp/rl.log 2>&1 &)
sleep 12
ros2 topic list
for t in /JOINTS_DATA /JOINTS_CMD /IMU_DATA; do
  echo -n "$t "; timeout 6 ros2 topic hz $t 2>&1 | grep average | tail -1
done
