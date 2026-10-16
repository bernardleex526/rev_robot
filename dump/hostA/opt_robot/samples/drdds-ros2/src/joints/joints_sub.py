import rclpy
from rclpy.node import Node
from drdds.msg import JointsData

class JointsDataSubscriber(Node):
    def __init__(self):
        super().__init__('jointsdata_subscriber')
        self.subscription = self.create_subscription(
            JointsData,
            '/JOINTS_DATA',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg: JointsData):
        # 打印 joints_data 数组长度
        print(f"Received JointsData message: {len(msg.data.joints_data)}")
        # 遍历每个 joint
        for joint in msg.data.joints_data:
            print(f" - Position: {joint.position:.6f}, "
                  f"Torque: {joint.torque:.6f}, "
                  f"Velocity: {joint.velocity:.6f}")

def main(args=None):
    rclpy.init(args=args)
    node = JointsDataSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
