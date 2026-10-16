#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import ParameterEvent
from rcl_interfaces.srv import GetParameters, SetParameters
from rcl_interfaces.msg import ParameterValue


class ParamsServer(Node):
    def __init__(self):
        super().__init__('params_server_py')
        
        # Declare parameters
        self.declare_parameter('device_name', 'default_device')
        self.declare_parameter('update_rate', 10)
        self.declare_parameter('enable_debug', False)
        self.declare_parameter('max_distance', 100.0)
        
        self.get_logger().info("===== ROS2 Parameters Server (Python) =====")
        self.get_logger().info("Parameters Server started successfully!")
        self.get_logger().info("\n--- Declared Parameters ---")
        self.get_logger().info(f"  device_name: {self.get_parameter('device_name').value}")
        self.get_logger().info(f"  update_rate: {self.get_parameter('update_rate').value}")
        self.get_logger().info(f"  enable_debug: {self.get_parameter('enable_debug').value}")
        self.get_logger().info(f"  max_distance: {self.get_parameter('max_distance').value}")
        
        # Subscribe to parameter events
        self.param_event_sub = self.create_subscription(
            ParameterEvent,
            '/parameter_events',
            self.param_event_callback,
            10
        )
        
        # Create a timer to periodically show parameters
        self.timer = self.create_timer(5.0, self.timer_callback)
        
        self.print_usage()
    
    def param_event_callback(self, msg: ParameterEvent):
        """Handle parameter change events"""
        if msg.changed_parameters:
            self.get_logger().info("\n--- Parameters Changed ---")
            for param in msg.changed_parameters:
                self.get_logger().info(f"Parameter '{param.name}' changed")
                self.get_logger().info(f"  New value: {param.value}")
    
    def timer_callback(self):
        """Display current parameter values"""
        self.get_logger().info("\n--- Current Parameter Values ---")
        self.get_logger().info(f"  device_name: {self.get_parameter('device_name').value}")
        self.get_logger().info(f"  update_rate: {self.get_parameter('update_rate').value}")
        self.get_logger().info(f"  enable_debug: {self.get_parameter('enable_debug').value}")
        self.get_logger().info(f"  max_distance: {self.get_parameter('max_distance').value}")
    
    def print_usage(self):
        """Print available CLI commands"""
        self.get_logger().info("\n========================================")
        self.get_logger().info("Available CLI Commands:")
        self.get_logger().info("========================================")
        self.get_logger().info("\n1. List all parameters:")
        self.get_logger().info("   ros2 param list")
        
        self.get_logger().info("\n2. Get a specific parameter:")
        self.get_logger().info("   ros2 param get /params_server_py device_name")
        self.get_logger().info("   ros2 param get /params_server_py update_rate")
        self.get_logger().info("   ros2 param get /params_server_py enable_debug")
        self.get_logger().info("   ros2 param get /params_server_py max_distance")
        
        self.get_logger().info("\n3. Set a string parameter:")
        self.get_logger().info("   ros2 param set /params_server_py device_name my_device")
        
        self.get_logger().info("\n4. Set an integer parameter:")
        self.get_logger().info("   ros2 param set /params_server_py update_rate 20")
        
        self.get_logger().info("\n5. Set a boolean parameter:")
        self.get_logger().info("   ros2 param set /params_server_py enable_debug true")
        
        self.get_logger().info("\n6. Set a float parameter:")
        self.get_logger().info("   ros2 param set /params_server_py max_distance 50.5")
        
        self.get_logger().info("\n7. Load parameters from YAML file:")
        self.get_logger().info("   ros2 param load /params_server_py params.yaml")
        
        self.get_logger().info("\n8. Save parameters to YAML file:")
        self.get_logger().info("   ros2 param dump /params_server_py > params.yaml")
        
        self.get_logger().info("\n========================================\n")


def main(args=None):
    rclpy.init(args=args)
    node = ParamsServer()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
