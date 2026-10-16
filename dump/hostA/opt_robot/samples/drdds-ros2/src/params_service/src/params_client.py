#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rcl_interfaces.srv import GetParameters, SetParameters
from rcl_interfaces.msg import Parameter, ParameterValue


class ParamsClient(Node):
    def __init__(self):
        super().__init__('params_client_py')
        
        # Create clients for parameter operations
        self.get_params_client = self.create_client(GetParameters, '/params_server_py/get_parameters')
        self.set_params_client = self.create_client(SetParameters, '/params_server_py/set_parameters')
        
        self.get_logger().info("===== ROS2 Parameters Client (Python) =====")
        self.get_logger().info("Parameters Client initialized!")
    
    def get_parameter(self, param_name):
        """Get a specific parameter value"""
        request = GetParameters.Request()
        request.names = [param_name]
        
        while not self.get_params_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting again...')
        
        future = self.get_params_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            if future.result().values:
                return future.result().values[0]
        return None
    
    def set_parameter(self, param_name, value):
        """Set a parameter value"""
        param = Parameter()
        param.name = param_name
        param.value = ParameterValue()
        
        # Determine value type
        if isinstance(value, bool):
            param.value.type = ParameterValue.TYPE_BOOL
            param.value.bool_value = value
        elif isinstance(value, int):
            param.value.type = ParameterValue.TYPE_INTEGER
            param.value.integer_value = value
        elif isinstance(value, float):
            param.value.type = ParameterValue.TYPE_DOUBLE
            param.value.double_value = value
        else:
            param.value.type = ParameterValue.TYPE_STRING
            param.value.string_value = str(value)
        
        request = SetParameters.Request()
        request.parameters = [param]
        
        while not self.set_params_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Service not available, waiting again...')
        
        future = self.set_params_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None:
            self.get_logger().info(f"Parameter '{param_name}' set successfully!")
        else:
            self.get_logger().error(f"Failed to set parameter '{param_name}'")


def main(args=None):
    rclpy.init(args=args)
    client = ParamsClient()
    
    # Example usage
    client.get_logger().info("\n--- Example: Get parameter 'device_name' ---")
    result = client.get_parameter('device_name')
    if result:
        client.get_logger().info(f"device_name = {result}")
    
    client.get_logger().info("\n--- Example: Set parameter 'update_rate' to 30 ---")
    client.set_parameter('update_rate', 30)
    
    rclpy.shutdown()


if __name__ == '__main__':
    main()
