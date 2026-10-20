#!/usr/bin/env python3
"""Record /JOINTS_CMD and /JOINTS_DATA to CSV for offline comparison between simulators.

  record_joints.py out_prefix seconds
"""
import sys
import time

import rclpy
from rclpy.node import Node

from drdds.msg import ImuData, JointsData, JointsDataCmd


def main():
    prefix, secs = sys.argv[1], float(sys.argv[2])
    rclpy.init()
    n = Node("m20_record")
    t0 = time.time()
    f_cmd = open(prefix + "_cmd.csv", "w")
    f_dat = open(prefix + "_dat.csv", "w")
    f_imu = open(prefix + "_imu.csv", "w")

    def on_cmd(m):
        j = m.data.joints_data
        f_cmd.write(f"{time.time() - t0:.4f}," + ",".join(
            f"{x.position:.4f},{x.velocity:.4f},{x.kp:.1f},{x.kd:.2f},{x.torque:.3f}" for x in j) + "\n")

    def on_dat(m):
        j = m.data.joints_data
        f_dat.write(f"{time.time() - t0:.4f}," + ",".join(
            f"{x.position:.4f},{x.velocity:.4f},{x.torque:.3f}" for x in j) + "\n")

    def on_imu(m):
        d = m.data
        f_imu.write(f"{time.time() - t0:.4f},{d.roll:.3f},{d.pitch:.3f},{d.yaw:.3f},"
                    f"{d.omega_x:.4f},{d.omega_y:.4f},{d.omega_z:.4f},{d.acc_x:.3f},{d.acc_y:.3f},{d.acc_z:.3f}\n")

    n.create_subscription(JointsDataCmd, "/JOINTS_CMD", on_cmd, 200)
    n.create_subscription(JointsData, "/JOINTS_DATA", on_dat, 200)
    n.create_subscription(ImuData, "/IMU_DATA", on_imu, 200)
    while time.time() - t0 < secs:
        rclpy.spin_once(n, timeout_sec=0.01)
    for f in (f_cmd, f_dat, f_imu):
        f.close()
    n.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
