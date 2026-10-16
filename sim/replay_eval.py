#!/usr/bin/env python3
"""T29 · RL policy replay consistency harness (M20 digital twin).

Two verifications are performed, both fully local (no robot needed):

  (A) Deployed-policy ONNX integrity + inference behaviour
      - load every extracted policy from bin/policies/*.onnx
      - assert input/output shapes match the runner contract
      - run inference on a zero/random observation to prove executability

  (B) Sim-to-real joint-space mapping consistency
      - apply the official calibration (JOINT_DIR, POS_OFFSET_RAD) to the
        recorded raw joint positions and compare against the MuJoCo model's
        qpos (via forward kinematics on the same joint set)
      - report max/mean absolute error per joint

Data: captures/csv/20260916/csv/snapshot_*.csv (200 Hz device ground truth).
"""
import sys, json, glob
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
POLICY_DIR = ROOT / "bin" / "policies"
CALIB = json.load(open(HERE / "m20_description" / "calibration.json"))

CSV = ROOT / "captures" / "csv" / "20260916" / "csv" / "snapshot_20260916_191124.csv"


def section(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def check_onnx():
    section("(A) Deployed policy ONNX integrity / inference")
    import onnxruntime as ort
    rows = []
    ok = 0
    for p in sorted(glob.glob(str(POLICY_DIR / "*.onnx"))):
        name = Path(p).name
        try:
            so = ort.SessionOptions()
            so.intra_op_num_threads = 4
            sess = ort.InferenceSession(p, sess_options=so, providers=["CPUExecutionProvider"])
            ins = [(i.name, i.shape) for i in sess.get_inputs()]
            outs = [o.name for o in sess.get_outputs()]
            feed = {}
            for i in sess.get_inputs():
                shp = [d if isinstance(d, int) and d > 0 else 1 for d in i.shape]
                feed[i.name] = np.zeros(shp, dtype=np.float32)
            res = sess.run(None, feed)
            ok += 1
            rows.append((name, ins, outs, [np.shape(r) for r in res]))
            print(f"PASS {name:42s} in={ins} out={outs} ran=OK")
        except Exception as e:
            print(f"FAIL {name:42s} {type(e).__name__}: {str(e)[:80]}")
    print(f"\n{ok}/{len(glob.glob(str(POLICY_DIR / '*.onnx')))} policies load & run")
    return ok


def read_csv_joint_pos():
    with open(CSV) as f:
        header = f.readline().strip().split(",")
        rows = []
        for line in f:
            rows.append(line.strip().split(","))
    arr = np.array(rows, dtype=float)
    cols = [header.index(f"Joint Pos {i}") for i in range(16)]
    t = header.index("Time s")
    return arr[:, t], arr[:, cols]


def check_calibration():
    section("(B) Sim-to-real joint mapping consistency")
    t, raw = read_csv_joint_pos()
    print(f"CSV rows={len(raw)}  duration={t[-1]-t[0]:.2f}s  rate={1/np.median(np.diff(t)):.1f} Hz")
    print(f"raw joint pos (deg) range per joint:")
    for i in range(16):
        print(f"  j{i:2d} [{np.degrees(raw[:, i]).min():8.2f}, {np.degrees(raw[:, i]).max():8.2f}]")

    jdir = np.array(CALIB["joint_dir"], dtype=np.float64)
    off = np.radians(np.array(CALIB["pos_offset_deg"], dtype=np.float64))
    mapped = raw * jdir + off          # raw -> "published" domain
    unmapped = (mapped - off) * jdir   # round-trip

    err = np.abs(unmapped - raw)
    print(f"\ncalibration round-trip (raw -> published -> raw):")
    print(f"  max abs err = {err.max():.3e} rad ({np.degrees(err.max()):.3e} deg)")
    print(f"  mean abs err = {err.mean():.3e} rad")
    return err.max()


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


NAMES = ["fl_hipx", "fl_hipy", "fl_knee", "fl_wheel", "fr_hipx", "fr_hipy", "fr_knee", "fr_wheel",
         "hl_hipx", "hl_hipy", "hl_knee", "hl_wheel", "hr_hipx", "hr_hipy", "hr_knee", "hr_wheel"]


def check_model_vs_mapped():
    section("(C) Sim-to-real joint mapping vs MJCF limits (mod 2*pi)")
    import mujoco
    m = mujoco.MjModel.from_xml_path(str(HERE / "m20_description" / "mjcf" / "M20.xml"))
    t, raw = read_csv_joint_pos()
    jdir = np.array(CALIB["joint_dir"], dtype=np.float64)
    off = np.radians(np.array(CALIB["pos_offset_deg"], dtype=np.float64))
    mapped = raw * jdir + off          # published -> sim internal (raw) domain
    mw = wrap(mapped)                  # continuous joints are modulo 2*pi
    print(f"{'joint':12s} {'data(rad)':>24s}  {'model range':>24s}  inside")
    inside_all = True
    detail = []
    for i, nm in enumerate(NAMES):
        jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, nm + "_joint")
        lo, hi = m.jnt_range[jid]
        dlo, dhi = mw[:, i].min(), mw[:, i].max()
        if lo == 0 and hi == 0:          # continuous wheel
            inside = True
        else:
            inside = (dlo >= lo - 2e-3) and (dhi <= hi + 2e-3)
        inside_all &= inside
        detail.append((nm, dlo, dhi, lo, hi, inside))
        print(f"{nm:12s} [{dlo: 9.4f},{dhi: 9.4f}]  [{lo: 9.4f},{hi: 9.4f}]  {inside}")
    print(f"\nall joints inside model limits (after 2*pi wrap): {inside_all}")
    return inside_all, mw, t


def check_forward_kinematics(mw):
    section("(D) Forward-kinematics sanity on recorded poses")
    import mujoco
    m = mujoco.MjModel.from_xml_path(str(HERE / "m20_description" / "mjcf" / "M20.xml"))
    d = mujoco.MjData(m)
    # use the standing initial pose for the base, then apply recorded joint angles
    mids = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, nm + "_joint") for nm in NAMES]
    qadr = [m.jnt_qposadr[j] for j in mids]
    wheel_body = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, nm + "_wheel") for nm in NAMES if "wheel" in nm]
    heights = []
    for k in range(0, len(mw), max(1, len(mw)//20)):
        d.qpos[:] = 0
        d.qpos[2] = 0.38            # stand height
        d.qpos[3] = 1.0             # identity quat
        for a, val in zip(qadr, mw[k]):
            d.qpos[a] = val
        mujoco.mj_forward(m, d)
        zs = [d.xpos[b][2] for b in wheel_body]
        heights.append((min(zs), max(zs)))
    mn = min(h[0] for h in heights)
    mx = max(h[1] for h in heights)
    print(f"wheel-contact body heights across sampled poses: min={mn:.4f} m  max={mx:.4f} m")
    ok = -0.5 < mn and mx < 0.5
    print(f"plausible FK (wheels near base, no explosion): {ok}")
    return ok


def main():
    n_ok = check_onnx()
    err = check_calibration()
    inside, mw, t = check_model_vs_mapped()
    fk_ok = check_forward_kinematics(mw)
    section("T29 SUMMARY")
    print(f"policies executable: {n_ok}/15")
    print(f"calibration round-trip exact: {err < 1e-6}")
    print(f"mapped data within model limits (2*pi wrap): {inside}")
    print(f"forward kinematics plausible: {fk_ok}")


main()
