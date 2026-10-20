#!/usr/bin/env python3
"""Ground-truth base pose of the M20.

Gazebo: /gazebo/get_entity_state.  MuJoCo: /m20/base_pose (published by run_mujoco_bridge.py).

  base_pose.py            # print once
  base_pose.py watch 10   # print every second for 10 s
"""
import math
import sys
import time

import rclpy
from gazebo_msgs.srv import GetEntityState
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node


def show(p, q):
    zz = 1 - 2 * (q.x * q.x + q.y * q.y)
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, zz))))
    print(f"base xyz= {p.x:7.3f} {p.y:7.3f} {p.z:6.3f}   tilt={tilt:5.1f} deg", flush=True)


def main():
    rclpy.init()
    n = Node("m20_base_pose")
    latest = {}
    n.create_subscription(PoseStamped, "/m20/base_pose", lambda m: latest.update(pose=m.pose), 10)
    cli = n.create_client(GetEntityState, "/gazebo/get_entity_state")
    end_wait = time.time() + 5.0
    while time.time() < end_wait and "pose" not in latest and not cli.service_is_ready():
        rclpy.spin_once(n, timeout_sec=0.1)
    if "pose" not in latest and not cli.service_is_ready():
        print("no ground truth: neither /gazebo/get_entity_state nor /m20/base_pose available")
        return
    secs = float(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "watch" else 0.0
    end = time.time() + secs
    while True:
        if cli.service_is_ready():
            fut = cli.call_async(GetEntityState.Request(name="m20", reference_frame="world"))
            rclpy.spin_until_future_complete(n, fut, timeout_sec=2.0)
            r = fut.result()
            if r and r.success:
                show(r.state.pose.position, r.state.pose.orientation)
        else:
            rclpy.spin_once(n, timeout_sec=0.2)
            if "pose" in latest:
                show(latest["pose"].position, latest["pose"].orientation)
        if time.time() >= end:
            break
        time.sleep(1.0)
    n.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
