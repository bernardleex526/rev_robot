#!/bin/bash
# Rebuild only m20_gazebo from the Windows source copy (fast iteration).
set -e
W=${W:-~/m20_sim_ws}
SIM_SRC=${SIM_SRC:-$(cd "$(dirname "$0")" && pwd)}
rm -rf "$W/src/m20_gazebo"
cp -r "$SIM_SRC/m20_gazebo" "$W/src/"
find "$W/src/m20_gazebo" -type f \( -name '*.py' -o -name '*.cpp' -o -name '*.txt' -o -name '*.xml' -o -name '*.world' -o -name '*.in' \) -exec sed -i 's/\r$//' {} +
chmod +x "$W"/src/m20_gazebo/scripts/*.py
cd "$W"
source /opt/ros/humble/setup.bash
source install/setup.bash
colcon build --packages-select m20_gazebo --cmake-args -DCMAKE_BUILD_TYPE=Release \
  -DM20_MJCF="$W/src/M20_sdk_deploy/M20_description/m20_mjcf/mjcf/M20.xml" 2>&1 | grep -vE '^\[|^$' | tail -15
