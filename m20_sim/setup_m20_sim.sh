#!/bin/bash
# One-shot setup of the M20 simulation workspace in WSL (ROS 2 Humble, Gazebo Classic 11, MuJoCo).
#   REPO=/mnt/e/ccmax/rev_robot SIM_SRC=$REPO/m20_sim W=~/m20_sim_ws bash setup_m20_sim.sh
# Builds: drdds (rebuilt from dumped .msg/.srv), m20_sdk_deploy (official SDK, patched for ROS-topic
# commands, x86), m20_gazebo (URDF + Gazebo plugin). Re-runnable.
set -e
REPO=${REPO:-$(cd "$(dirname "$0")/.." && pwd)}
SIM_SRC=${SIM_SRC:-$REPO/m20_sim}
W=${W:-~/m20_sim_ws}
SDK_SRC="$REPO/dump/hostA/home_user/sdk_deploy/src/M20_sdk_deploy"
mkdir -p "$W/src"

echo "== drdds"
rm -rf "$W/src/drdds" && mkdir -p "$W/src/drdds"
cp -r "$REPO/dump/hostA/ros_foxy_share/msg" "$REPO/dump/hostA/ros_foxy_share/srv" "$REPO/dump/hostA/ros_foxy_share/package.xml" "$W/src/drdds/"
rm -f "$W"/src/drdds/msg/*.idl "$W"/src/drdds/srv/*.idl
(
  cd "$W/src/drdds"
  {
    echo 'cmake_minimum_required(VERSION 3.8)'
    echo 'project(drdds)'
    echo 'find_package(ament_cmake REQUIRED)'
    echo 'find_package(rosidl_default_generators REQUIRED)'
    echo 'find_package(builtin_interfaces REQUIRED)'
    echo 'find_package(geometry_msgs REQUIRED)'
    echo 'rosidl_generate_interfaces(${PROJECT_NAME}'
    for f in msg/*.msg srv/*.srv; do echo "  \"$f\""; done
    echo '  DEPENDENCIES builtin_interfaces geometry_msgs)'
    echo 'ament_export_dependencies(rosidl_default_runtime)'
    echo 'ament_package()'
  } > CMakeLists.txt
  grep -q geometry_msgs package.xml || sed -i 's#<build_depend>rosidl_default_generators</build_depend>#<build_depend>rosidl_default_generators</build_depend>\n  <depend>builtin_interfaces</depend>\n  <depend>geometry_msgs</depend>#' package.xml
)

echo "== m20_sdk_deploy (patched)"
rm -rf "$W/src/M20_sdk_deploy"
cp -r "$SDK_SRC" "$W/src/"
tr -d '\r' < "$SIM_SRC/sdk_patch/ros_cmd_interface.hpp" > "$W/.ros_cmd_interface.hpp"
mkdir -p "$W/.patch" && cp "$W/.ros_cmd_interface.hpp" "$W/.patch/ros_cmd_interface.hpp"
tr -d '\r' < "$SIM_SRC/sdk_patch/apply_sdk_patch.py" > "$W/.patch/apply_sdk_patch.py"
python3 -I "$W/.patch/apply_sdk_patch.py" "$W/src/M20_sdk_deploy"

echo "== m20_gazebo"
rm -rf "$W/src/m20_gazebo"
cp -r "$SIM_SRC/m20_gazebo" "$W/src/"
find "$W/src/m20_gazebo" -type f \( -name '*.py' -o -name '*.cpp' -o -name '*.txt' -o -name '*.xml' -o -name '*.world' -o -name '*.in' \) -exec sed -i 's/\r$//' {} +
chmod +x "$W"/src/m20_gazebo/scripts/*.py

# libevdev is only needed at link time by the SDK's keyboard backend
if [ ! -e /usr/lib/x86_64-linux-gnu/libevdev.so ]; then
  mkdir -p "$W/.deps" && cd "$W/.deps"
  [ -e root/usr/lib/x86_64-linux-gnu/libevdev.so ] || { apt-get download libevdev-dev libevdev2 >/dev/null; for d in *.deb; do dpkg -x "$d" root; done; }
  export LIBRARY_PATH="$W/.deps/root/usr/lib/x86_64-linux-gnu:$LIBRARY_PATH"
fi

cd "$W"
set +u
source /opt/ros/humble/setup.bash
colcon build --parallel-workers 4 --packages-select drdds
source install/setup.bash
colcon build --parallel-workers 4 --packages-select m20_sdk_deploy m20_gazebo \
  --cmake-args -DBUILD_PLATFORM=x86 -DCMAKE_BUILD_TYPE=Release \
  -DM20_MJCF="$W/src/M20_sdk_deploy/M20_description/m20_mjcf/mjcf/M20.xml"

cat > "$W/env.sh" <<EOF
source /opt/ros/humble/setup.bash
source $W/install/setup.bash
source /usr/share/gazebo/setup.sh
export GAZEBO_PLUGIN_PATH=$W/install/m20_gazebo/lib:\$GAZEBO_PLUGIN_PATH
export GAZEBO_MODEL_PATH=$W/install/m20_gazebo/share:\$GAZEBO_MODEL_PATH
[ -d $W/.deps ] && export LD_LIBRARY_PATH=$W/.deps/root/usr/lib/x86_64-linux-gnu:\$LD_LIBRARY_PATH
# python with mujoco/scipy for the MuJoCo bridge (system python keeps rclpy)
[ -d ~/.venvs/m20 ] && export PYTHONPATH=\$PYTHONPATH:\$(~/.venvs/m20/bin/python -c 'import site;print(site.getsitepackages()[0])')
export ROS_DOMAIN_ID=\${ROS_DOMAIN_ID:-1}
export M20_SDK_DIR=$W/src/M20_sdk_deploy
EOF
echo "== done. Use: source $W/env.sh"
