#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from drdds.msg import Joints
from drdds.msg import JointValue
from builtin_interfaces.msg import Time as BuiltinTime


class JointsPublisher(Node):
    def __init__(self):
        super().__init__('joints_publisher')
        self.publisher_ = self.create_publisher(Joints, '/JOINTS', 10)
        # 创建一个200Hz的定时器 (每5毫秒发布一次)
        self.timer = self.create_timer(0.005, self.timer_callback)
        self.counter = 0

    def timer_callback(self):
        msg = Joints()
        
        # 设置消息头
        msg.header.frame_id = 0
        current_time = self.get_clock().now()
        msg.header.stamp = BuiltinTime(sec=current_time.seconds_nanoseconds()[0], 
                                      nanosec=current_time.seconds_nanoseconds()[1])
        
        # 创建一些示例关节数据
        # 这里我们创建4个关节的示例数据
        for i in range(4):
            joint_value = JointValue()
            # joint_value.name = f'joint_{i}'
            joint_value.data_id = i
            joint_value.status_word = 1  # 示例状态字
            joint_value.position = 0.5 + 0.1 * i + 0.05 * self.counter
            joint_value.torque = 0.1 + 0.01 * i
            joint_value.velocity = 0.05 + 0.005 * i
            joint_value.motion_temp = 30.0 + i
            joint_value.driver_temp = 35.0 + i
            
            msg.data.append(joint_value)
        
        # 发布消息
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing Joints: {len(msg.data)} joints')
        self.counter += 1


def main(args=None):
    rclpy.init(args=args)
    publisher = JointsPublisher()
    
    try:
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()