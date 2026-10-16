import rclpy
from rclpy.node import Node
from drdds.srv import StdSrvInt32  # 与 C++ 中的 drdds::srv::StdSrvInt32 对应

class CommandService(Node):
    def __init__(self):
        super().__init__('command_service')
        # 创建服务
        self.srv = self.create_service(
            StdSrvInt32,
            '/client',
            self.handle_command)
        self.get_logger().info('Service server ready.')

    def handle_command(self, request, response):
        # 打印请求内容
        self.get_logger().info(f"Received command: {request.command}")
        # 简单逻辑：返回相同的数值
        response.result = request.command
        self.get_logger().info(f"Returning result: {response.result}")
        return response

def main(args=None):
    rclpy.init(args=args)
    node = CommandService()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
