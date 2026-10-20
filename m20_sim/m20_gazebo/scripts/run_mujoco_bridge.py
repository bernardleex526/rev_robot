#!/usr/bin/env python3
"""Run the official SDK MuJoCo bridge with extras for algorithm testing, without modifying it.

  run_mujoco_bridge.py [--headless] [--scene flat|stair] [--rtf-sleep]

Adds on top of interface/robot/simulation/mujoco_simulation_ros2.py:
  - /m20/base_pose (geometry_msgs/PoseStamped, 50 Hz): ground-truth base pose for evaluation
  - --headless: no viewer (WSL without GUI / CI)
  - --scene flat: M20.xml (empty floor) instead of M20_stair.xml
"""
import argparse
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--scene", choices=["flat", "stair"], default="stair")
    ap.add_argument("--sdk", default=os.environ.get("M20_SDK_DIR", ""),
                    help="path to M20_sdk_deploy (default: $M20_SDK_DIR)")
    args = ap.parse_args()

    sdk = Path(args.sdk).resolve()
    sim_py = sdk / "interface/robot/simulation/mujoco_simulation_ros2.py"
    if not sim_py.is_file():
        sys.exit(f"cannot find {sim_py}; pass --sdk or set M20_SDK_DIR")

    spec = importlib.util.spec_from_file_location("m20_mujoco_sim", sim_py)
    sim = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sim)

    sim.USE_VIEWER = not args.headless
    xml = "M20.xml" if args.scene == "flat" else "M20_stair.xml"
    sim.XML_PATH = str(sdk / "M20_description/m20_mjcf/mjcf" / xml)

    import time

    import mujoco
    import rclpy
    from geometry_msgs.msg import PoseStamped

    class Bridge(sim.MuJoCoSimulationNode):
        def __init__(self):
            super().__init__(xml_path=sim.XML_PATH)
            self.pose_pub = self.create_publisher(PoseStamped, "/m20/base_pose", 10)

        def start(self):
            # The SDK loop advances at most one 1 ms step per iteration and never catches up, so
            # sim time drifts behind wall time whenever ROS callbacks stall; rl_deploy runs on wall
            # time, and the resulting time scaling destabilises the policy. Step in catch-up batches.
            step = 0
            t0 = time.perf_counter()
            last_report, last_report_step = t0, 0
            while rclpy.ok():
                due = int((time.perf_counter() - t0) / sim.DT)
                n = min(due - step, 50)
                for _ in range(n):
                    step += 1
                    self._apply_joint_torque()
                    mujoco.mj_step(self.model, self.data)
                    self.timestamp = step * sim.DT
                    if step % 5 == 0:
                        self._publish_robot_state(step)
                    if self.viewer and step % sim.RENDER_INTERVAL == 0:
                        self.viewer.sync()
                if due - step > 200:
                    # fell far behind (e.g. process suspended): drop the backlog instead of fast-forwarding
                    t0 = time.perf_counter() - step * sim.DT
                rclpy.spin_once(self, timeout_sec=0.0 if n else 0.0005)
                now = time.perf_counter()
                if now - last_report >= 10.0:
                    rtf = (step - last_report_step) * sim.DT / (now - last_report)
                    print(f"[run_mujoco_bridge] sim_time={step * sim.DT:7.1f}s  real_time_factor={rtf:.2f}", flush=True)
                    last_report, last_report_step = now, step

        def _publish_robot_state(self, step):
            super()._publish_robot_state(step)
            if step % 20 == 0:
                q = self.data.qpos
                m = PoseStamped()
                m.header.frame_id = "world"
                m.header.stamp.sec = int(self.timestamp)
                m.header.stamp.nanosec = int((self.timestamp - int(self.timestamp)) * 1e9)
                m.pose.position.x, m.pose.position.y, m.pose.position.z = (float(v) for v in q[0:3])
                m.pose.orientation.w, m.pose.orientation.x, m.pose.orientation.y, m.pose.orientation.z = (
                    float(v) for v in q[3:7])
                self.pose_pub.publish(m)

    np.set_printoptions(precision=4, suppress=True)
    rclpy.init()
    node = Bridge()
    print(f"[run_mujoco_bridge] scene={xml} viewer={sim.USE_VIEWER}", flush=True)
    try:
        node.start()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
