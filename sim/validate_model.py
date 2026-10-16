#!/usr/bin/env python3
"""Validate the M20 MuJoCo digital-twin model against expected structure."""
import sys, json
import mujoco
from pathlib import Path

HERE = Path(__file__).resolve().parent
XML = HERE / "m20_description" / "mjcf" / "M20.xml"

m = mujoco.MjModel.from_xml_path(str(XML))
fails = []

def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)

check(m.nu == 16, f"actuator count == 16 (got {m.nu})")
check(m.nbody == 18, f"body count == 18 (got {m.nbody})")
check(30.0 <= m.body_mass.sum() <= 40.0, f"total mass in [30,40] kg (got {m.body_mass.sum():.3f})")

expected = {
    "fl_hipx_joint": (-0.436, 0.611), "fl_hipy_joint": (-2.286, 2.583), "fl_knee_joint": (-2.809, 2.792),
    "fr_hipx_joint": (-0.611, 0.436), "fr_hipy_joint": (-2.286, 2.583), "fr_knee_joint": (-2.809, 2.792),
    "hl_hipx_joint": (-0.436, 0.611), "hl_hipy_joint": (-2.583, 2.286), "hl_knee_joint": (-2.792, 2.809),
    "hr_hipx_joint": (-0.611, 0.436), "hr_hipy_joint": (-2.583, 2.286), "hr_knee_joint": (-2.792, 2.809),
}
for i in range(m.njnt):
    nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, i)
    if nm in expected:
        lo, hi = expected[nm]
        r = m.jnt_range[i]
        check(abs(r[0]-lo) < 1e-3 and abs(r[1]-hi) < 1e-3, f"{nm} range {r} == ({lo},{hi})")

# model must be step-able
data = mujoco.MjData(m)
for _ in range(200):
    mujoco.mj_step(m, data)
check(True, "200 mj_step iterations without error")

print(f"\n{'ALL PASS' if not fails else str(len(fails)) + ' FAILURES'}")
sys.exit(1 if fails else 0)
