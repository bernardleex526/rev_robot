#!/usr/bin/env python3
"""Patch the official M20_sdk_deploy so rl_deploy can take commands from ROS topics.

Selects the user-command source at runtime with M20_CMD_SOURCE=ros|keyboard|gamepad (default ros).
Usage: python3 apply_sdk_patch.py <path/to/M20_sdk_deploy>
"""
import shutil
import sys
from pathlib import Path


def replace_once(path: Path, old: str, new: str):
    text = path.read_text()
    if new in text:
        return
    if old not in text:
        sys.exit(f"patch anchor not found in {path}:\n{old}")
    path.write_text(text.replace(old, new, 1))


def main():
    sdk = Path(sys.argv[1]).resolve()
    here = Path(__file__).resolve().parent
    shutil.copy(here / "ros_cmd_interface.hpp", sdk / "interface/user_command/ros_cmd_interface.hpp")

    replace_once(sdk / "include/types/custom_types.h",
                 "        kKeyBoard = 0,\n        kGamepad,\n",
                 "        kKeyBoard = 0,\n        kGamepad,\n        kRosTopic,\n")

    sm = sdk / "state_machine/quadruped_wheel/qw_state_machine.hpp"
    replace_once(sm, '#include "keyboard_interface.hpp"\n',
                 '#include "keyboard_interface.hpp"\n#include "ros_cmd_interface.hpp"\n')
    replace_once(sm,
                 "            uc_ptr_ = gp_ptr;\n        }else{",
                 "            uc_ptr_ = gp_ptr;\n"
                 "        }else if(remote_cmd_type_ == RemoteCommandType::kRosTopic){\n"
                 "            uc_ptr_ = std::make_shared<RosCmdInterface>(robot_name_);\n"
                 "        }else{")

    main_cpp = sdk / "main.cpp"
    replace_once(main_cpp,
                 "    std::shared_ptr<StateMachineBase> fsm = std::make_shared<qw::QwStateMachine>(RobotName::M20, RemoteCommandType::kGamepad);",
                 "    const char* src_env = std::getenv(\"M20_CMD_SOURCE\");\n"
                 "    std::string src = src_env ? src_env : \"ros\";\n"
                 "    RemoteCommandType rct = src == \"keyboard\" ? RemoteCommandType::kKeyBoard\n"
                 "                          : src == \"gamepad\"  ? RemoteCommandType::kGamepad\n"
                 "                                                : RemoteCommandType::kRosTopic;\n"
                 "    std::cout << \"Command source: \" << src << std::endl;\n"
                 "    std::shared_ptr<StateMachineBase> fsm = std::make_shared<qw::QwStateMachine>(RobotName::M20, rct);")

    cm = sdk / "CMakeLists.txt"
    replace_once(cm, "find_package(drdds REQUIRED)\n",
                 "find_package(drdds REQUIRED)\nfind_package(geometry_msgs REQUIRED)\nfind_package(std_msgs REQUIRED)\n")
    replace_once(cm, "ament_target_dependencies(rl_deploy\n  rclcpp\n  drdds\n)",
                 "ament_target_dependencies(rl_deploy\n  rclcpp\n  drdds\n  geometry_msgs\n  std_msgs\n)")

    pkg = sdk / "package.xml"
    text = pkg.read_text()
    if "<depend>geometry_msgs</depend>" not in text:
        anchor = "<buildtool_depend>ament_cmake</buildtool_depend>"
        if anchor not in text:
            sys.exit(f"patch anchor not found in {pkg}")
        pkg.write_text(text.replace(anchor, anchor + "\n  <depend>geometry_msgs</depend>\n  <depend>std_msgs</depend>", 1))
    print("SDK patched:", sdk)


if __name__ == "__main__":
    main()
