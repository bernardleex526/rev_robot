#!/usr/bin/env python3
"""In-process MuJoCo sim for the M20: fast, deterministic, the stable path for algorithm testing.

Policy contract identical to the official SDK (m20_policy_runner.hpp); verified against
sim2sim_stand_sdk.py in the reverse-engineering repo (stands, walks ~0.5 m/s, tilt < 4 deg).

  mujoco_inproc.py --policy policy.onnx [--vx 0.6] [--wz 0] [--secs 10] [--scene flat|stair] [--viewer]

To test your own controller, replace `controller()` (gets the state dict, returns goal_pos/goal_vel/kp/kd
in robot order, MJCF domain) - the rest stays the same.
"""
import argparse
import time
from pathlib import Path

import mujoco
import numpy as np

SIM_DT = 0.001  # 1 kHz physics
ROBOT_ORDER = ["fl_hipx", "fl_hipy", "fl_knee", "fl_wheel", "fr_hipx", "fr_hipy", "fr_knee", "fr_wheel",
               "hl_hipx", "hl_hipy", "hl_knee", "hl_wheel", "hr_hipx", "hr_hipy", "hr_knee", "hr_wheel"]
POLICY_ORDER = ["fl_hipx", "fl_hipy", "fl_knee", "fr_hipx", "fr_hipy", "fr_knee",
                "hl_hipx", "hl_hipy", "hl_knee", "hr_hipx", "hr_hipy", "hr_knee",
                "fl_wheel", "fr_wheel", "hl_wheel", "hr_wheel"]
R2P = [ROBOT_ORDER.index(n) for n in POLICY_ORDER]
P2R = [POLICY_ORDER.index(n) for n in ROBOT_ORDER]

KP = np.array([80, 80, 80, 0.] * 4)
KD = np.array([2, 2, 2, .6] * 4)
ACT_SCALE = np.array([0.125, 0.25, 0.25, 5] * 4)
DEF_POLICY = np.array([0, -.6, 1., 0, -.6, 1., 0, .6, -1., 0, .6, -1., 0, 0, 0, 0])
DEF_ROBOT = np.array([0, -.6, 1., 0, 0, -.6, 1., 0, 0, .6, -1., 0, 0, .6, -1., 0])
TAU_LIMIT = np.array([76.4, 76.4, 76.4, 21.6] * 4)


def quat_to_R(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


class SdkPolicy:
    """The official SDK RL policy (57-dim obs). Swap this class out for your own controller."""

    def __init__(self, onnx_path):
        import onnxruntime as ort
        self.s = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        self.iname = self.s.get_inputs()[0].name
        self.last_action = np.zeros(16)

    def __call__(self, st, cmd):
        R = quat_to_R(st["quat"])
        jp = st["q"][R2P].copy()
        jp[12:16] = 0.0
        jp -= DEF_POLICY
        obs = np.concatenate([st["gyro"] * 0.25, R.T @ np.array([0, 0, -1.0]), cmd,
                              jp, st["dq"][R2P] * 0.05, self.last_action]).astype(np.float32)
        act = self.s.run(None, {self.iname: obs.reshape(1, 57)})[0].reshape(-1)
        self.last_action = act.copy()
        tmp = act[P2R] * ACT_SCALE + DEF_ROBOT
        goal_pos, goal_vel = tmp.copy(), np.zeros(16)
        for i in range(4):
            goal_vel[i * 4 + 3] = tmp[i * 4 + 3]
            goal_pos[i * 4 + 3] = st["q"][i * 4 + 3]  # wheels: velocity only
        return goal_pos, goal_vel, KP, KD


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--mjcf-dir", default=str(Path(__file__).resolve().parent.parent / "mjcf"),
                    help="directory with M20.xml / M20_stair.xml")
    ap.add_argument("--scene", choices=["flat", "stair"], default="flat")
    ap.add_argument("--vx", type=float, default=0.0)
    ap.add_argument("--vy", type=float, default=0.0)
    ap.add_argument("--wz", type=float, default=0.0)
    ap.add_argument("--secs", type=float, default=10.0)
    ap.add_argument("--policy-hz", type=float, default=50.0,
                    help="policy rate; the SDK runs it at 50 Hz (decimation 4 on a 5 ms loop)")
    ap.add_argument("--viewer", action="store_true", help="realtime viewer (needs WSLg)")
    ap.add_argument("--csv", help="write t,x,y,z,tilt per 10 ms to this file")
    a = ap.parse_args()

    xml = Path(a.mjcf_dir) / ("M20.xml" if a.scene == "flat" else "M20_stair.xml")
    m = mujoco.MjModel.from_xml_path(str(xml))
    m.opt.timestep = SIM_DT
    d = mujoco.MjData(m)
    jid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n + "_joint") for n in ROBOT_ORDER]
    qadr = np.array([m.jnt_qposadr[j] for j in jid])
    vadr = np.array([m.jnt_dofadr[j] for j in jid])
    aid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, n + "_joint") for n in ROBOT_ORDER]

    d.qpos[:] = 0
    d.qpos[2] = 0.45
    d.qpos[3] = 1.0
    d.qpos[qadr] = DEF_ROBOT
    mujoco.mj_forward(m, d)

    controller = SdkPolicy(a.policy)
    cmd = np.array([a.vx, a.vy, a.wz])
    goal_pos, goal_vel, kp, kd = DEF_ROBOT.copy(), np.zeros(16), KP, KD

    viewer = mujoco.viewer.launch_passive(m, d) if a.viewer else None
    out = open(a.csv, "w") if a.csv else None
    decimation = max(1, round(1.0 / (a.policy_hz * SIM_DT)))
    n = int(a.secs / SIM_DT)
    max_tilt, t_wall = 0.0, time.time()
    for k in range(n):
        q, dq = d.qpos[qadr], d.qvel[vadr]
        if k % decimation == 0:
            st = {"q": q.copy(), "dq": dq.copy(), "quat": d.sensordata[0:4].copy(),
                  "acc": d.sensordata[4:7].copy(), "gyro": d.sensordata[7:10].copy(),
                  "base_pos": d.qpos[0:3].copy()}
            goal_pos, goal_vel, kp, kd = controller(st, cmd)
        tau = np.clip(kp * (goal_pos - q) + kd * (goal_vel - dq), -TAU_LIMIT, TAU_LIMIT)
        d.ctrl[aid] = tau
        mujoco.mj_step(m, d)
        if k % 10 == 0:
            qw, qx, qy, qz = d.qpos[3:7]
            tilt = float(np.degrees(np.arccos(np.clip(1 - 2 * (qx * qx + qy * qy), -1, 1))))
            max_tilt = max(max_tilt, tilt)
            if out:
                out.write(f"{k * SIM_DT:.3f},{d.qpos[0]:.4f},{d.qpos[1]:.4f},{d.qpos[2]:.4f},{tilt:.2f}\n")
            if viewer:
                viewer.sync()
                lag = k * SIM_DT - (time.time() - t_wall)
                if lag > 0:
                    time.sleep(lag)
    # tilt only: absolute height is terrain-dependent (the stair scene climbs to ~1.1 m)
    held = max_tilt < 60 and d.qpos[2] > 0.15
    print(f"{'HELD' if held else 'FELL'}  t={a.secs}s  xy=({d.qpos[0]:+.3f},{d.qpos[1]:+.3f})  "
          f"z={d.qpos[2]:.3f}  max_tilt={max_tilt:.1f} deg  wall={time.time() - t_wall:.1f}s")
    return 0 if held else 1


if __name__ == "__main__":
    import mujoco.viewer  # noqa: F401  (registers viewer submodule)
    raise SystemExit(main())
