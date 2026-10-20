#!/usr/bin/env python3
"""Command helper for the patched rl_deploy (works with MuJoCo and Gazebo alike).

  m20_cmd.py stand            # target_mode 1 (only from WaitingForStand)
  m20_cmd.py rl               # target_mode 6 (only from StandingUp)
  m20_cmd.py damp             # target_mode 2
  m20_cmd.py vel 0.5 0 0 [secs]   # forward/side/yaw scales in [-1,1], streamed at 20 Hz
  m20_cmd.py demo             # stand -> rl -> walk forward 5 s -> turn 3 s -> stop, then prints the base state
  m20_cmd.py status           # print IMU rpy and joint positions once
"""
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import UInt8

from drdds.msg import ImuData, JointsData

MODES = {"stand": 1, "rl": 6, "damp": 2}


class Cmd(Node):
    def __init__(self):
        super().__init__("m20_cmd")
        self.mode_pub = self.create_publisher(UInt8, "/sim_mode", 10)
        self.vel_pub = self.create_publisher(Twist, "/sim_cmd", 10)
        self.imu = None
        self.joints = None
        self.create_subscription(ImuData, "/IMU_DATA", lambda m: setattr(self, "imu", m), 10)
        self.create_subscription(JointsData, "/JOINTS_DATA", lambda m: setattr(self, "joints", m), 10)

    def wait_for_subscriber(self, pub, timeout=5.0):
        end = time.time() + timeout
        while pub.get_subscription_count() == 0 and time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
        return pub.get_subscription_count() > 0

    def mode(self, name):
        if not self.wait_for_subscriber(self.mode_pub):
            self.get_logger().error("no subscriber on /sim_mode - is the patched rl_deploy running?")
            return
        for _ in range(3):
            self.mode_pub.publish(UInt8(data=MODES[name]))
            rclpy.spin_once(self, timeout_sec=0.05)
        print(f"sent mode {name} ({MODES[name]})")

    def vel(self, fx, fy, wz, secs):
        self.wait_for_subscriber(self.vel_pub)
        t = Twist()
        t.linear.x, t.linear.y, t.angular.z = fx, fy, wz
        end = time.time() + secs
        while time.time() < end:
            self.vel_pub.publish(t)
            rclpy.spin_once(self, timeout_sec=0.05)
        self.vel_pub.publish(Twist())

    def status(self, wait=2.0):
        end = time.time() + wait
        while (self.imu is None or self.joints is None) and time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
        if self.imu is None:
            print("no /IMU_DATA")
            return
        d = self.imu.data
        print(f"rpy(deg)= {d.roll:7.2f} {d.pitch:7.2f} {d.yaw:7.2f}   acc_z={d.acc_z:6.2f}")
        if self.joints:
            q = [j.position for j in self.joints.data.joints_data]
            print("joint pos:", " ".join(f"{x:6.2f}" for x in q))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    rclpy.init()
    n = Cmd()
    c = sys.argv[1]
    if c in MODES:
        n.mode(c)
    elif c == "vel":
        fx, fy, wz = (float(x) for x in sys.argv[2:5])
        secs = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
        n.vel(fx, fy, wz, secs)
    elif c == "status":
        n.status()
    elif c == "demo":
        n.mode("stand")
        time.sleep(4.0)
        n.status()
        n.mode("rl")
        time.sleep(2.0)
        n.vel(0.6, 0.0, 0.0, 5.0)
        n.vel(0.0, 0.0, 0.6, 3.0)
        time.sleep(1.0)
        n.status()
    else:
        print(__doc__)
    n.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
