#!/usr/bin/env python3
"""
Advanced Parameters Usage Example
展示在实际应用中如何使用ROS2参数进行动态重配置
"""

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rcl_interfaces.msg import ParameterEvent
import time


class AdvancedParamsExample(Node):
    def __init__(self):
        super().__init__('advanced_params_example')
        
        # Create callback group for handling concurrent callbacks
        callback_group = ReentrantCallbackGroup()
        
        # Declare parameters with descriptors (更详细的参数声明)
        param_descriptor = {
            'description': 'Robot device name',
            'type': 'string',
            'read_only': False,
        }
        self.declare_parameter('device_name', 'robot_1', param_descriptor)
        
        # Add parameter validate callback
        self.add_on_set_parameters_callback(self.params_callback)
        
        # Subscribe to parameter events to monitor changes
        self.param_event_sub = self.create_subscription(
            ParameterEvent,
            '/parameter_events',
            self.param_event_callback,
            10,
            callback_group=callback_group
        )
        
        # Create a timer for main application logic
        self.timer = self.create_timer(
            1.0,
            self.on_timer,
            callback_group=callback_group
        )
        
        self.last_device_name = None
        self.config_update_count = 0
        
        self.get_logger().info("Advanced Parameters Example initialized!")
        self.print_current_config()
    
    def params_callback(self, params):
        """
        Validate and process parameter changes
        Return SetParametersResult to accept or reject changes
        """
        from rcl_interfaces.srv import SetParameters
        from rclpy.parameter import Parameter
        
        for param in params:
            if param.name == 'device_name':
                if not isinstance(param.value, str) or len(param.value) == 0:
                    from rcl_interfaces.msg import SetParametersResult
                    result = SetParametersResult()
                    result.successful = False
                    result.reason = "device_name must be a non-empty string"
                    return [result]
                
                self.get_logger().info(f"Device name changed: {param.value}")
                self.config_update_count += 1
                self.on_device_config_update(param.value)
        
        from rcl_interfaces.msg import SetParametersResult
        result = SetParametersResult()
        result.successful = True
        return [result]
    
    def param_event_callback(self, msg: ParameterEvent):
        """Handle parameter change events"""
        for changed_param in msg.changed_parameters:
            self.get_logger().warning(
                f"🔔 Parameter '{changed_param.name}' changed "
                f"(Total updates: {self.config_update_count})"
            )
    
    def on_device_config_update(self, new_device_name):
        """Called when device configuration is updated"""
        self.get_logger().info(f"🔧 Applying new device configuration: {new_device_name}")
        # Here you would apply the new configuration
        # For example: reinitialize sensors, update device drivers, etc.
        time.sleep(0.5)  # Simulate configuration process
        self.get_logger().info(f"✅ Device '{new_device_name}' configured successfully!")
    
    def on_timer(self):
        """Main application loop"""
        current_device = self.get_parameter('device_name').value
        
        if current_device != self.last_device_name:
            self.last_device_name = current_device
            self.get_logger().info(f"📱 Currently using device: {current_device}")
        
        # Application-specific logic here
        # self.do_some_work()
    
    def print_current_config(self):
        """Print current configuration"""
        self.get_logger().info("\n" + "="*50)
        self.get_logger().info("Current Configuration:")
        self.get_logger().info("="*50)
        self.get_logger().info(f"device_name: {self.get_parameter('device_name').value}")
        self.get_logger().info("="*50 + "\n")


def main(args=None):
    rclpy.init(args=args)
    node = AdvancedParamsExample()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down...")
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
