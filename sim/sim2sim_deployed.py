#!/usr/bin/env python3
"""Run the REAL deployed M20 policy (joint-major 53-dim obs, 5-frame history) in MuJoCo.

Reverse-engineered contract (see analysis/24_obs_layout_extrinsic.md):
  obs_dim_ = 53, obs_history_num_ = 5, obs_total_dim_ = 318
  per-frame = [ omega*0.25 (3) | R^T*g (3) | cmd*scale (3)
              | dof_pos_jointmajor(12) - dof_pos_default_trans(12)
              | dof_vel_jointmajor(12)*0.05 | wheel_vel(4)*wscale | last_action(16, joint-major) ]
  action(16, joint-major) ->
      goal_pos[leg*4+j] = action[j*4+leg]*0.25 + dof_pos_default_[leg*3+j]   (j=0..2)
      goal_vel[leg*4+3] = 10.0 * action[12+leg]
      tau = kp*(goal_pos - pos) + kd*(goal_vel - vel)
"""
import sys, json, time
from pathlib import Path
import numpy as np
import mujoco

HERE = Path(__file__).resolve().parent
XML = HERE / "m20_description" / "mjcf" / "M20.xml"
CAL = json.load(open(HERE / "m20_description" / "calibration.json"))
RUNNER_PARAMS = json.load(open(HERE / "runner_params.json"))

SIM_DT, DECIMATION = 0.001, 20   # decimation_ = 20 -> policy at 50 Hz
ROBOT_ORDER = ["fl_hipx","fl_hipy","fl_knee","fl_wheel","fr_hipx","fr_hipy","fr_knee","fr_wheel",
               "hl_hipx","hl_hipy","hl_knee","hl_wheel","hr_hipx","hr_hipy","hr_knee","hr_wheel"]

# --- values read from PolicyRunnerBase / M20NaviStairRunner constructors (Ghidra) ---
OMEGA_SCALE   = 0.25
DOF_VEL_SCALE = 0.05
WHEEL_VEL_SCALE = 0.05
ACTION_SCALE  = 0.25
WHEEL_ACT_SCALE = 10.0
CMD_VEL_SCALE = np.array([1.0, 1.0, 0.25])   # cmd_vel_scale_ (base ctor)
KP = np.array([80,80,80,0.]*4)
KD = np.array([3,3,3,.6]*4)
DOF_POS_DEFAULT = np.array([-0.1,-0.8,1.6,  0.1,-0.8,1.6,  -0.1,0.8,-1.6,  0.1,0.8,-1.6])   # leg-major
DOF_POS_DEFAULT_TRANS = np.array([-0.1,0.1,-0.1,0.1, -0.8,-0.8,0.8,0.8, 1.6,1.6,-1.6,-1.6])  # joint-major
# Variant A = update_joint_data (joint-major obs, joint-major action)
# Variant B = gym_update_joint_data (leg-major obs, robot-order action)  e.g. M20BasicPlatRunner
# Per-runner observation spec (from GetRobotAction decompilation).
#   order: "joint" = joint-major dof_pos + joint-major action (update_joint_data)
#          "leg"   = leg-major dof_pos + robot-order action  (gym_update_joint_data)
#   gait:  insert sin(2*pi*phase), cos(2*pi*phase), gait_commands(5) after cmd
#   pre / post: extra constant appended after cmd / after last_action
RUNNER_SPEC = {
    "M20BasicPlatRunner": {"order": "leg", "gait": False, "pre": None, "post": None},   # 53
    "M20NaviFlatPolicyRunner": {"order": "joint", "gait": False, "pre": 0.52, "post": None},  # 54
    "M20NaviChargePolicyRunner": {"order": "joint", "gait": True, "pre": None, "post": None,
                                  "warmup": True},  # 60
    "M20StandPolicyRunner": {"order": "leg", "gait": True, "pre": None, "post": 1.0},   # 61
    "M20FinetuneStandRunner": {"order": "leg", "gait": False, "pre": None, "post": None},
    "M20SixAxisStandRunner": {"order": "leg", "gait": False, "pre": None, "post": None},
    "M20ExtrePolicyRunner": {"order": "leg", "gait": False, "pre": None, "post": None},
    "M20StepMoveRunner": {"order": "leg", "gait": False, "pre": None, "post": None},
    "M20HeightGapPolicyRunner": {"order": "joint", "gait": False, "pre": None, "post": None,
                                 "hmap": 451},  # 41*11, obs_dim=504, total=3024
}
DEFAULT_SPEC = {"order": "joint", "gait": False, "pre": None, "post": None}   # 53
# Values read directly from the constructors (CommaInitializer order is reliable there).
RUNNER_OVERRIDE = {
    "M20NaviChargePolicyRunner": {"kp": [60, 60, 60, 0], "kd": [1.5, 1.5, 1.5, 0.6],
                                  "gait_commands": [1.5, 0.5, 0.0, 0.0, 0.5]},
    "M20StandPolicyRunner": {"kp": [80, 100, 100, 0], "kd": [2.0, 2.0, 2.0, 0.6],
                             "gait_commands": [2.0, 0.5, 0.0, 0.0, 0.5]},
}
GAIT_DT = 0.02
GAIT_2PI = 6.283185307179586
HMAP_SCALE = 5.0
SPEC = dict(DEFAULT_SPEC)
obs_dim = 53


def apply_runner_params(name):
    """Override module-level constants from the decompiled per-runner values."""
    global OMEGA_SCALE, DOF_VEL_SCALE, WHEEL_VEL_SCALE, ACTION_SCALE, WHEEL_ACT_SCALE
    global DOF_POS_DEFAULT, DOF_POS_DEFAULT_TRANS, KP, KD, SPEC, obs_dim
    SPEC = dict(RUNNER_SPEC.get(name, DEFAULT_SPEC))
    ov = RUNNER_OVERRIDE.get(name, {})
    if "kp" in ov:
        KP = np.array([float(x) for x in (ov["kp"] * 4)])
    if "kd" in ov:
        KD = np.array([float(x) for x in (ov["kd"] * 4)])
    obs_dim = 53 + (2 + 5 if SPEC["gait"] else 0) + (1 if SPEC["pre"] is not None else 0) \
        + (1 if SPEC["post"] is not None else 0) + SPEC.get("hmap", 0)
    rp = RUNNER_PARAMS.get(name)
    if rp is None:
        print(f"[warn] runner params for '{name}' not found; using NaviStair defaults")
        return 53
    if rp.get("omega_scale_"): OMEGA_SCALE = rp["omega_scale_"]
    if rp.get("dof_vel_scale_"): DOF_VEL_SCALE = rp["dof_vel_scale_"]
    if rp.get("wheel_vel_scale_"): WHEEL_VEL_SCALE = rp["wheel_vel_scale_"]
    if rp.get("action_scale_"): ACTION_SCALE = rp["action_scale_"]
    if rp.get("wheel_action_scale_"): WHEEL_ACT_SCALE = rp["wheel_action_scale_"]
    d = rp.get("dof_pos_default")
    if d and len(d) == 12:
        DOF_POS_DEFAULT = np.array(d)
    elif d and len(d) >= 15:            # 16-element (4 per leg, incl. wheels) -> legs only
        arr = np.array(list(d) + [0.0] * (16 - len(d)))[:16]
        DOF_POS_DEFAULT = arr.reshape(4, 4)[:, :3].reshape(-1)
    dt = rp.get("dof_pos_default_trans")
    if dt and len(dt) == 12:
        DOF_POS_DEFAULT_TRANS = np.array(dt)
    print(f"[runner] {name}: omega={OMEGA_SCALE} dof_vel={DOF_VEL_SCALE} wheel_vel={WHEEL_VEL_SCALE} "
          f"act={ACTION_SCALE} wheel_act={WHEEL_ACT_SCALE}")
    print(f"[runner]   default={list(DOF_POS_DEFAULT)}")
    return 53


def quat_to_R(q):
    w, x, y, z = q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def joint_major(robot_order_vec):
    """robot order [FL3,FW, FR3,FW, HL3,HW, HR3,HW] -> joint-major [hipx*4, hipy*4, knee*4] (12)"""
    legs = np.array(robot_order_vec).reshape(4, 4)
    return np.concatenate([legs[:, 0], legs[:, 1], legs[:, 2]])


def leg_major_legs(robot_order_vec):
    """robot order -> leg-major legs only [FL3, FR3, HL3, HR3] (12)"""
    legs = np.array(robot_order_vec).reshape(4, 4)
    return legs[:, :3].reshape(-1)


def main():
    import onnxruntime as ort
    pol = sys.argv[1] if len(sys.argv) > 1 else "bin/policies/policy_m20_navi_stair_v7_0_himloco.onnx"
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
    vx  = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    runner = sys.argv[4] if len(sys.argv) > 4 else "M20NaviStairRunner"
    apply_runner_params(runner)
    p = HERE.parent / pol
    s = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
    iname = s.get_inputs()[0].name
    ishape = s.get_inputs()[0].shape
    print(f"policy={p.name} in={iname}{ishape} vx={vx} dur={dur}s")
    MULTI = len(s.get_inputs()) > 1
    if MULTI:
        # state [1,H,53] + command [1,N] + uncertain [1,1]
        n_hist = int(ishape[1])
        obs_total = n_hist * obs_dim
        cmd_dim = int(s.get_inputs()[1].shape[1])
        print(f"MULTI spec={SPEC} obs_dim={obs_dim} history={n_hist} command_dim={cmd_dim}")
    else:
        obs_total = int(ishape[1])
        n_hist = obs_total // obs_dim - 1
        cmd_dim = 0
        print(f"spec={SPEC} obs_dim={obs_dim} history={n_hist} total={obs_total}")

    m = mujoco.MjModel.from_xml_path(str(XML)); m.opt.timestep = SIM_DT
    d = mujoco.MjData(m)
    jid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n+"_joint") for n in ROBOT_ORDER]
    qadr = [m.jnt_qposadr[j] for j in jid]; vadr = [m.jnt_dofadr[j] for j in jid]

    stand = DOF_POS_DEFAULT.copy()
    d.qpos[:] = 0; d.qpos[2] = 0.45; d.qpos[3] = 1.0
    for leg in range(4):
        for j in range(3):
            d.qpos[qadr[leg*4 + j]] = DOF_POS_DEFAULT[leg*3 + j]
    mujoco.mj_forward(m, d)

    last_action = np.zeros(16)
    gait_phase = 0.05
    gait_commands = np.zeros(5)
    _ov = RUNNER_OVERRIDE.get(runner, {})
    if "gait_commands" in _ov:
        gait_commands = np.array(_ov["gait_commands"], dtype=np.float64)
    if len(sys.argv) > 5:
        gait_commands[0] = float(sys.argv[5])
    history = np.zeros((n_hist, obs_dim))
    goal_pos = np.array([0.1,-0.8,1.6,0.,  0.1,-0.8,1.6,0.,  -0.1,0.8,-1.6,0.,  0.1,0.8,-1.6,0.])
    goal_pos = np.zeros(16)
    for leg in range(4):
        goal_pos[leg*4:leg*4+3] = DOF_POS_DEFAULT[leg*3:leg*3+3]
    goal_vel = np.zeros(16)
    cmd = np.array([vx, 0.0, 0.0]); hist = []
    policy_step = 0
    n = int(dur/SIM_DT); t0 = time.time()
    for k in range(n):
        if k % DECIMATION == 0:
            q = np.array([d.qpos[a] for a in qadr]); v = np.array([d.qvel[a] for a in vadr])
            quat = d.sensordata[0:4]; gyro = d.sensordata[7:10]
            R = quat_to_R(quat)
            omega = gyro * OMEGA_SCALE
            grav = R.T @ np.array([0.0,0.0,-1.0])
            dof_pos_jm = joint_major(q) - DOF_POS_DEFAULT_TRANS
            dof_vel_jm = joint_major(v) * DOF_VEL_SCALE
            if SPEC["order"] == "leg":
                dof_pos_jm = leg_major_legs(q) - DOF_POS_DEFAULT
                dof_vel_jm = leg_major_legs(v) * DOF_VEL_SCALE
            wheel_vel = np.array([v[leg*4+3] for leg in range(4)]) * WHEEL_VEL_SCALE
            cur = np.concatenate([omega, grav, cmd*CMD_VEL_SCALE])
            if SPEC["gait"]:
                phase = (gait_phase * GAIT_DT) % 1.0
                gait_phase = phase
                cur = np.concatenate([cur, [np.sin(phase*GAIT_2PI), np.cos(phase*GAIT_2PI)],
                                      gait_commands])
            if SPEC["pre"] is not None:
                cur = np.concatenate([cur, [SPEC["pre"]]])
            cur = np.concatenate([cur, dof_pos_jm, dof_vel_jm, wheel_vel, last_action])
            if SPEC["post"] is not None:
                cur = np.concatenate([cur, [SPEC["post"]]])
            if SPEC.get("hmap"):
                cur = np.concatenate([cur, np.zeros(SPEC["hmap"]) * HMAP_SCALE])
            if k < 3:
                print(f"  [comp] omega={np.round(omega,3)} grav={np.round(grav,3)}")
                print(f"  [comp] dof_pos_jm={np.round(dof_pos_jm,3)}")
                print(f"  [comp] dof_vel_jm={np.round(dof_vel_jm,3)} wheel_vel={np.round(wheel_vel,3)}")
                print(f"  [comp] q_raw={np.round(q,3)}")
            if MULTI:
                history = np.vstack([history[1:], cur]) if n_hist > 0 else history
                cmd_vec = np.zeros((1, cmd_dim), dtype=np.float32)
                if cmd_dim > 0:
                    cmd_vec[0, 0] = vx
                feed = {iname: history.reshape(1, n_hist, obs_dim).astype(np.float32),
                        "command": cmd_vec,
                        "uncertain": np.ones((1, 1), dtype=np.float32)}
                act = s.run(None, feed)[0].reshape(-1)
            else:
                obs = np.concatenate([cur, history.reshape(-1)]).astype(np.float32)
                act = s.run(None, {iname: obs.reshape(1, obs_total)})[0].reshape(-1)
            act = np.clip(act, -100.0, 100.0)   # PolicyRunnerBase: LimitNumber(action_, -100, 100)
            if k < 20 or k % 1000 == 0:
                print(f"  [dbg] t={k*SIM_DT:.3f} act[min,max]=[{act.min():.3f},{act.max():.3f}]")
            last_action = act.copy()
            history = np.vstack([history[1:], cur]) if n_hist > 0 else history
            policy_step += 1
            for leg in range(4):
                for j in range(3):
                    if SPEC["order"] == "leg":
                        goal_pos[leg*4+j] = act[leg*4+j]*ACTION_SCALE + DOF_POS_DEFAULT[leg*3+j]
                    else:
                        goal_pos[leg*4+j] = act[j*4+leg]*ACTION_SCALE + DOF_POS_DEFAULT[leg*3+j]
                goal_vel[leg*4+3] = WHEEL_ACT_SCALE * act[(leg*4+3) if SPEC["order"] == "leg" else (12+leg)]
        q = np.array([d.qpos[a] for a in qadr]); v = np.array([d.qvel[a] for a in vadr])
        kp_eff, kd_eff = KP, KD
        if SPEC.get("warmup") and policy_step <= n_hist * 2:
            kp_eff, kd_eff = KP * 0.5, KD * 2.0
        d.ctrl[:] = np.clip(kp_eff*(goal_pos-q) + kd_eff*(goal_vel-v), -80, 80)
        mujoco.mj_step(m, d)
        if k % 200 == 0:
            qw,qx,qy,qz = d.qpos[3:7]
            tilt = np.degrees(np.arccos(np.clip(1-2*(qx*qx+qy*qy),-1,1)))
            hist.append((k*SIM_DT, d.qpos[2], tilt, d.qpos[0], d.qpos[1]))

    zs=[h[1] for h in hist]; tl=[h[2] for h in hist]
    settle = [h for h in hist if h[0] >= 2.0]
    zs2 = [h[1] for h in settle] or zs
    tl2 = [h[2] for h in settle] or tl
    ok = all(0.15 < z < 0.85 for z in zs2) and max(tl2) < 60
    print(f"\nran {dur}s in {time.time()-t0:.1f}s wall")
    print(f"height z: min={min(zs):.3f} max={max(zs):.3f} end={zs[-1]:.3f}")
    print(f"tilt deg: max={max(tl):.2f} end={tl[-1]:.2f}")
    print(f"final xy=({hist[-1][3]:+.3f},{hist[-1][4]:+.3f})")
    print(f"{'HELD' if ok else 'FELL'} for {dur:.0f}s")
    for t,z,a,x,y in hist[::max(1,len(hist)//10)]:
        print(f"  t={t:6.2f} z={z:.3f} tilt={a:5.2f} x={x:+.3f} y={y:+.3f}")
    return 0 if ok else 1


sys.exit(main())
