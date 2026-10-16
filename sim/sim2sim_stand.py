#!/usr/bin/env python3
"""T32 · Stand the M20 digital twin in simulation with the deployed RL policy.

Faithful re-implementation of the official m20_policy_runner.hpp:
  obs[57] = [omega*0.25, R^T*g, cmd, (jpos_policy-default), jvel_policy*0.05, last_action]
  action[16] -> scale(robot) -> + default(robot) -> goal joint pos/vel
  PD: kp=[80,80,80,0]x4 kd=[2,2,2,0.6]x4   policy 50 Hz, sim 1000 Hz

Runs headless and reports base height / attitude over the run.
"""
import sys, json, time
from pathlib import Path
import numpy as np
import mujoco

HERE = Path(__file__).resolve().parent
XML = HERE / "m20_description" / "mjcf" / "M20.xml"
CAL = json.load(open(HERE / "m20_description" / "calibration.json"))

SIM_DT = 0.001
DECIMATION = 4                       # policy at 50 Hz

ROBOT_ORDER = ["fl_hipx", "fl_hipy", "fl_knee", "fl_wheel",
               "fr_hipx", "fr_hipy", "fr_knee", "fr_wheel",
               "hl_hipx", "hl_hipy", "hl_knee", "hl_wheel",
               "hr_hipx", "hr_hipy", "hr_knee", "hr_wheel"]
POLICY_ORDER = ["fl_hipx", "fl_hipy", "fl_knee", "fr_hipx", "fr_hipy", "fr_knee",
                "hl_hipx", "hl_hipy", "hl_knee", "hr_hipx", "hr_hipy", "hr_knee",
                "fl_wheel", "fr_wheel", "hl_wheel", "hr_wheel"]

def perm(frm, to):
    idx = {n: i for i, n in enumerate(frm)}
    return [idx[n] for n in to]

R2P = perm(ROBOT_ORDER, POLICY_ORDER)
P2R = perm(POLICY_ORDER, ROBOT_ORDER)

KP = np.array([80, 80, 80, 0., 80, 80, 80, 0., 80, 80, 80, 0., 80, 80, 80, 0.])
KD = np.array([2, 2, 2, .6, 2, 2, 2, .6, 2, 2, 2, .6, 2, 2, 2, .6])
ACT_SCALE = np.array(CAL["action_scale_robot"], dtype=np.float64)
DEF_POLICY = np.array([0, -.6, 1., 0, -.6, 1., 0, .6, -1., 0, .6, -1., 0, 0, 0, 0], dtype=np.float64)
DEF_ROBOT = np.array(CAL["dof_default_robot"], dtype=np.float64)
J_DIR = np.array(CAL["joint_dir"], dtype=np.float64)
J_OFF = np.radians(np.array(CAL["pos_offset_deg"], dtype=np.float64))

POLICY = HERE.parent / "bin" / "policies" / "policy_m20_flat_v1_4.onnx"


def main():
    import onnxruntime as ort
    policy = sys.argv[1] if len(sys.argv) > 1 else "bin/policies/policy_m20_flat_v1_4.onnx"
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    p = HERE.parent / policy
    sess = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
    iname = sess.get_inputs()[0].name
    print(f"policy: {p.name}  input={iname}{sess.get_inputs()[0].shape}")

    m = mujoco.MjModel.from_xml_path(str(XML))
    m.opt.timestep = SIM_DT
    d = mujoco.MjData(m)
    bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "base_link")
    jid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n + "_joint") for n in ROBOT_ORDER]
    qadr = [m.jnt_qposadr[j] for j in jid]
    vadr = [m.jnt_dofadr[j] for j in jid]

    # initial standing pose (MJCF/raw convention)
    stand_raw = np.array(CAL["joint_init_rad"], dtype=np.float64)
    d.qpos[:] = 0
    d.qpos[2] = 0.30
    d.qpos[3] = 1.0
    for a, v in zip(qadr, stand_raw):
        d.qpos[a] = v
    mujoco.mj_forward(m, d)

    last_action = np.zeros(16)
    cmd = np.zeros(3)                      # zero velocity command (stand)
    hist = []
    n_steps = int(duration / SIM_DT)
    t0 = time.time()
    for step in range(n_steps):
        if step % DECIMATION == 0:
            qpos = np.array([d.qpos[a] for a in qadr])
            qvel = np.array([d.qvel[a] for a in vadr])
            # rotation matrix of base body
            R = d.xmat[bid].reshape(3, 3)
            omega = d.qvel[3:6]            # angular velocity (world) - approximate
            grav = R.T @ np.array([0, 0, -1.0])
            jpos_p = qpos[R2P] - DEF_POLICY
            jvel_p = qvel[R2P] * 0.05
            obs = np.concatenate([omega * 0.25, grav, cmd, jpos_p, jvel_p, last_action]).astype(np.float32)
            act = sess.run(None, {iname: obs.reshape(1, 57)})[0].reshape(-1)
            last_action = act.copy()
            tmp = np.array([act[P2R[i]] * ACT_SCALE[i] for i in range(16)]) + DEF_ROBOT
            goal_pos = tmp.copy()
            goal_vel = np.zeros(16)
            for i in range(4):
                goal_pos[i*4+3] = qpos[i*4+3]      # wheel pos unused
                goal_vel[i*4+3] = tmp[i*4+3]
        # PD torque
        qpos = np.array([d.qpos[a] for a in qadr])
        qvel = np.array([d.qvel[a] for a in vadr])
        tau = KP * (goal_pos - qpos) + KD * (goal_vel - qvel)
        tau = np.clip(tau, -60, 60)
        d.ctrl[:] = tau
        mujoco.mj_step(m, d)
        if step % 100 == 0:
            hist.append((step * SIM_DT, d.qpos[2], np.degrees(np.arccos(np.clip(1 - 2*(d.qpos[4]**2 + d.qpos[5]**2), -1, 1)))))

    zs = [h[1] for h in hist]
    rolls = [h[2] for h in hist]
    print(f"\nran {duration}s ({n_steps} steps) in {time.time()-t0:.1f}s wall")
    print(f"base height z: start={zs[0]:.3f} min={min(zs):.3f} max={max(zs):.3f} end={zs[-1]:.3f}")
    print(f"tilt(deg):     max={max(rolls):.2f}")
    survived = d.qpos[2] > 0.15 and max(rolls) < 60
    print(f"\nSTOOD {duration:.0f}s WITHOUT FALLING: {survived}")
    for t, z, tl in hist[::max(1, len(hist)//10)]:
        print(f"  t={t:6.2f}  z={z:.3f}  tilt={tl:5.2f}")


main()
