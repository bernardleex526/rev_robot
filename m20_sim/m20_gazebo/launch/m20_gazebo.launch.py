import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler,
                            SetEnvironmentVariable, TimerAction)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory("m20_gazebo")
    urdf_path = os.path.join(share, "urdf", "m20.urdf")
    with open(urdf_path) as f:
        robot_description = f.read()

    gui = LaunchConfiguration("gui")
    world = LaunchConfiguration("world")
    z = LaunchConfiguration("z")
    with_rl = LaunchConfiguration("rl_deploy")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("gazebo_ros"), "launch", "gazebo.launch.py")),
        launch_arguments={"world": world, "gui": gui, "verbose": "false"}.items(),
    )

    rsp = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description, "use_sim_time": True}],
        output="screen",
    )

    spawn = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-entity", "m20", "-topic", "robot_description", "-z", z, "-timeout", "120"],
        output="screen",
    )

    # rl_deploy blocks at startup until joint data flows, so start it only after the robot exists
    rl = Node(
        package="m20_sdk_deploy",
        executable="rl_deploy",
        output="screen",
        additional_env={"M20_CMD_SOURCE": "ros"},
        condition=IfCondition(with_rl),
    )
    start_rl_after_spawn = RegisterEventHandler(
        OnProcessExit(target_action=spawn, on_exit=[TimerAction(period=1.0, actions=[rl])]))

    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true"),
        DeclareLaunchArgument("world", default_value=os.path.join(share, "worlds", "m20_flat.world")),
        DeclareLaunchArgument("z", default_value="0.2", description="spawn height of base_link"),
        DeclareLaunchArgument("rl_deploy", default_value="false",
                              description="also start the official SDK controller (patched, ROS-topic commands)"),
        SetEnvironmentVariable("GAZEBO_MODEL_PATH",
                               os.path.dirname(share) + os.pathsep + os.environ.get("GAZEBO_MODEL_PATH", "")),
        gazebo,
        rsp,
        spawn,
        start_rl_after_spawn,
    ])
