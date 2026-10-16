from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    Launch the parameters server with initial configuration
    """
    params_config = {
        'device_name': 'robot_device',
        'update_rate': 15,
        'enable_debug': True,
        'max_distance': 75.5,
    }
    
    return LaunchDescription([
        Node(
            package='params_service',
            executable='params_server_cpp',
            name='params_server',
            parameters=[params_config],
            output='screen',
        ),
    ])
