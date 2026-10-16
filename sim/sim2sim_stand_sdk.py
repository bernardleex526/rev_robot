#!/usr/bin/env python3
"""T32 · Sim-to-sim standing/walking with the official M20 SDK RL policy.

Faithful reimplementation of:
  sdk_deploy/run_policy/m20_policy_runner.hpp           (obs/action glue)
  sdk_deploy/interface/robot/simulation/mujoco_simulation_ros2.py (control law)
  M20_description/m20_mjcf                              (model)

Convention note
  This MJCF is authored in the SDK "published" joint convention
  (front hipy<0 so thigh points down, knee>0 flees forward; rear signs mirrored),
  identical to m20_policy_runner's dof_default_eigen_robot. So:
        MJCF qpos == published joint angle   (no direction/offset conversion)
  The JOINT_DIR/POS_OFFSET_DEG table in the example script converts the *real*
  robot encoder frame to this same published frame and therefore does not apply
  to the MJCF.

  obs[57] = [omega*0.25 | R^T*g | cmd | jpos_policy-DEF_POLICY | jvel_policy*0.05 | last_action]
  action  -> *ACT_SCALE +DEF_ROBOT -> goal (legs: position, wheels: velocity)
  tau = kp*(goal_pos-qpos) + kd*(goal_vel-qvel)
  kp=[80,80,80,0]*4  kd=[2,2,2,0.6]*4   policy 50 Hz, sim 1000 Hz
"""
import sys, json, time
from pathlib import Path
import numpy as np
import mujoco

HERE = Path(__file__).resolve().parent
XML = HERE / "m20_description" / "mjcf" / "M20.xml"
CAL = json.load(open(HERE / "m20_description" / "calibration.json"))

SIM_DT, DECIMATION = 0.001, 4
ROBOT_ORDER = ["fl_hipx","fl_hipy","fl_knee","fl_wheel","fr_hipx","fr_hipy","fr_knee","fr_wheel",
               "hl_hipx","hl_hipy","hl_knee","hl_wheel","hr_hipx","hr_hipy","hr_knee","hr_wheel"]
POLICY_ORDER = ["fl_hipx","fl_hipy","fl_knee","fr_hipx","fr_hipy","fr_knee",
                "hl_hipx","hl_hipy","hl_knee","hr_hipx","hr_hipy","hr_knee",
                "fl_wheel","fr_wheel","hl_wheel","hr_wheel"]
def perm(f, t):
    d = {n: i for i, n in enumerate(f)}; return [d[n] for n in t]
R2P, P2R = perm(ROBOT_ORDER, POLICY_ORDER), perm(POLICY_ORDER, ROBOT_ORDER)

KP = np.array([80,80,80,0.]*4)
KD = np.array([2,2,2,.6]*4)
ACT_SCALE = np.array(CAL["action_scale_robot"], float)
DEF_POLICY = np.array([0,-.6,1.,0,-.6,1.,0,.6,-1.,0,.6,-1.,0,0,0,0], float)
DEF_ROBOT  = np.array(CAL["dof_default_robot"], float)

def quat_to_R(q):
    w,x,y,z = q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def main():
    import onnxruntime as ort
    pol = sys.argv[1] if len(sys.argv) > 1 else "dump/hostA/home_user/sdk_deploy/src/M20_sdk_deploy/policy/policy.onnx"
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    vx  = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    wz  = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    p = HERE.parent / pol
    s = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
    iname = s.get_inputs()[0].name
    print(f"policy={p.name} in={iname}{s.get_inputs()[0].shape} vx={vx} wz={wz} dur={dur}s")

    m = mujoco.MjModel.from_xml_path(str(XML)); m.opt.timestep = SIM_DT
    d = mujoco.MjData(m)
    jid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n+"_joint") for n in ROBOT_ORDER]
    qadr = [m.jnt_qposadr[j] for j in jid]; vadr = [m.jnt_dofadr[j] for j in jid]

    stand = DEF_ROBOT.copy()
    d.qpos[:] = 0; d.qpos[2] = 0.45; d.qpos[3] = 1.0
    for a, v in zip(qadr, stand): d.qpos[a] = v
    mujoco.mj_forward(m, d)

    last_action = np.zeros(16); goal_pos = stand.copy(); goal_vel = np.zeros(16)
    cmd = np.array([vx, 0.0, wz]); hist = []
    n = int(dur/SIM_DT); t0 = time.time()
    for k in range(n):
        if k % DECIMATION == 0:
            q = np.array([d.qpos[a] for a in qadr]); v = np.array([d.qvel[a] for a in vadr])
            quat = d.sensordata[0:4]; gyro = d.sensordata[7:10]
            R = quat_to_R(quat)
            omega = gyro * 0.25
            grav = R.T @ np.array([0.0,0.0,-1.0])
            jp = q[R2P].copy(); jp[12:16] = 0.0; jp -= DEF_POLICY
            jv = v[R2P] * 0.05
            obs = np.concatenate([omega, grav, cmd, jp, jv, last_action]).astype(np.float32)
            act = s.run(None, {iname: obs.reshape(1,57)})[0].reshape(-1)
            last_action = act.copy()
            tmp = np.array([act[P2R[i]]*ACT_SCALE[i] for i in range(16)]) + DEF_ROBOT
            goal_pos = tmp.copy(); goal_vel = np.zeros(16)
            for i in range(4):
                goal_vel[i*4+3] = tmp[i*4+3]
                goal_pos[i*4+3] = q[i*4+3]
        q = np.array([d.qpos[a] for a in qadr]); v = np.array([d.qvel[a] for a in vadr])
        d.ctrl[:] = np.clip(KP*(goal_pos-q) + KD*(goal_vel-v), -80, 80)
        mujoco.mj_step(m, d)
        if k % 200 == 0:
            qw,qx,qy,qz = d.qpos[3:7]
            tilt = np.degrees(np.arccos(np.clip(1-2*(qx*qx+qy*qy),-1,1)))
            hist.append((k*SIM_DT, d.qpos[2], tilt, d.qpos[0], d.qpos[1]))

    zs=[h[1] for h in hist]; tl=[h[2] for h in hist]
    # "not fallen": base stays within [0.15, 0.75] and tilt < 60 deg
    ok = all(0.15 < z < 0.80 for z in zs) and max(tl) < 60
    print(f"\nran {dur}s in {time.time()-t0:.1f}s wall")
    print(f"height z: min={min(zs):.3f} max={max(zs):.3f} end={zs[-1]:.3f}")
    print(f"tilt deg: max={max(tl):.2f} end={tl[-1]:.2f}")
    print(f"final xy=({hist[-1][3]:+.3f},{hist[-1][4]:+.3f})")
    print(f"\n{'HELD' if ok else 'FELL'} for {dur:.0f}s")
    for t,z,a,x,y in hist[::max(1,len(hist)//12)]:
        print(f"  t={t:6.2f} z={z:.3f} tilt={a:5.2f} x={x:+.3f} y={y:+.3f}")
    return 0 if ok else 1

sys.exit(main())
