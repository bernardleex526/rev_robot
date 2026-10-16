#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
import numpy as np
import struct
import math
from threading import Thread
import time

class LidarPublisher(Node):
    def __init__(self):
        super().__init__('lidar_publisher')
        self.publisher_ = self.create_publisher(PointCloud2, '/LIDAR_POINTS', 10)
        # Create a 10Hz timer (0.1 seconds)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.counter = 0
        
    def timer_callback(self):
        # Create point cloud with 170000 points
        num_points = 170
        
        # Generate point cloud data
        points = self.generate_point_cloud(num_points, self.counter)
        
        # Create PointCloud2 message
        msg = self.create_pointcloud2_msg(points)
        
        # Publish the message
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published point cloud with {num_points} points')
        self.counter += 1
    
    def generate_point_cloud(self, num_points, counter):
        """
        Generate sample point cloud data with specified number of points
        """
        # Create points in a spiral pattern with some noise
        points = []
        
        for i in range(num_points):
            # Create a spiral pattern
            angle = (i / 1000.0) + (counter / 10.0)
            radius = 5.0 + (i % 100) / 20.0
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            z = (i % 50) / 10.0 - 2.5  # Range from -2.5 to 2.5
            
            # Add some intensity value (0-255)
            intensity = int((math.sin(angle) + 1) * 127.5)
            
            points.append([x, y, z, float(intensity)])
            
        return points
    
    def create_pointcloud2_msg(self, points):
        """
        Create PointCloud2 message from points array
        Each point has x, y, z coordinates and intensity
        """
        msg = PointCloud2()
        
        # # Set header
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'lidar_frame'
        
        # Define point fields (x, y, z, intensity)
        msg.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name='intensity', offset=12, datatype=PointField.FLOAT32, count=1)
        ]
        
        # Set point properties
        msg.height = 1
        msg.width = len(points)
        msg.point_step = 16  # 4 floats (x,y,z,intensity) * 4 bytes each
        msg.row_step = msg.point_step * msg.width
        msg.is_dense = True  # No invalid points
        
        # Pack data into binary format
        buffer = []
        for point in points:
            buffer.append(struct.pack('ffff', point[0], point[1], point[2], point[3]))
        
        msg.data = b''.join(buffer)
        
        return msg

def main(args=None):
    rclpy.init(args=args)
    publisher = LidarPublisher()
    
    try:
        # 使用多线程执行器以更好地利用CPU
        from rclpy.executors import MultiThreadedExecutor
        executor = MultiThreadedExecutor(num_threads=2)
        executor.add_node(publisher)
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()