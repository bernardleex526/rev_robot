#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from drdds.msg import JointsCmd
from drdds.msg import JointCmdValue
from builtin_interfaces.msg import Time as BuiltinTime


class JointsCmdPublisher(Node):
    def __init__(self):
        super().__init__('joints_cmd_publisher')
        self.publisher_ = self.create_publisher(JointsCmd, '/JOINTS_CMD', 10)
        # 创建一个200Hz的定时器 (每5毫秒发布一次)
        self.timer = self.create_timer(0.005, self.timer_callback)
        self.counter = 0

    def timer_callback(self):
        msg = JointsCmd()
        
        # 设置消息头
        msg.header.frame_id = 0
        current_time = self.get_clock().now()
        msg.header.stamp = BuiltinTime(sec=current_time.seconds_nanoseconds()[0], 
                                      nanosec=current_time.seconds_nanoseconds()[1])
        
        # 创建一些示例关节命令数据
        # 这里我们创建4个关节的示例数据
        msg.data.resize(4)  
        for i in range(4):
            joint_cmd = JointCmdValue()
            # joint_cmd.name = f'joint_{i}'
            joint_cmd.data_id = i
            joint_cmd.control_word = 1  # 示例控制字
            joint_cmd.position = 0.5 + 0.1 * i + 0.05 * self.counter
            joint_cmd.torque = 0.1 + 0.01 * i
            joint_cmd.velocity = 0.05 + 0.005 * i
            joint_cmd.kp = 10.0
            joint_cmd.kd = 1.0
            
            msg.data.append(joint_cmd)
        
        # 发布消息
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing JointsCmd: {len(msg.data)} joints')
        self.counter += 1


def main(args=None):
    rclpy.init(args=args)
    publisher = JointsCmdPublisher()
    
    try:
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()