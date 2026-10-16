import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import Header  # 导入Header类型


class PointCloudSubscriber(Node):
    def __init__(self):
        super().__init__('pointcloud_subscriber')
        self.subscription = self.create_subscription(
            PointCloud2,
            '/LIDAR_POINTS',
            self.topic_callback,
            10
        )
        self.subscription  # 防止被垃圾回收

    def topic_callback(self, msg: PointCloud2):
        # 计算消息延迟
        current_time = self.get_clock().now()
        msg_time = rclpy.time.Time(seconds=msg.header.stamp.sec, nanoseconds=msg.header.stamp.nanosec)
        delay = (current_time - msg_time).nanoseconds / 1e9  # 转换为秒
        
        self.get_logger().info(
            f'Received message with delay: {delay:.6f} seconds'
        )
        self.get_logger().info(
            f'Width: {msg.width}, Height: {msg.height}, '
            f'Point step: {msg.point_step}, Row step: {msg.row_step}'
        )

        for field in msg.fields:
            self.get_logger().info(
                f' - Name: {field.name}, '
                f'Offset: {field.offset}, '
                f'Datatype: {field.datatype}, '
                f'Count: {field.count}'
            )


def main(args=None):
    rclpy.init(args=args)
    node = PointCloudSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()