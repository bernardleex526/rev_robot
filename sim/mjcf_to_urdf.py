#!/usr/bin/env python3
"""Convert the M20 MJCF (MJCF is the authoritative model) into a URDF for Gazebo.

Reads the MuJoCo model and emits a URDF with:
  - one link per body (visual mesh + collision primitive)
  - one joint per non-free joint (type/axis/limit copied from MuJoCo)
  - inertial (mass, com, inertia diag) copied from MuJoCo
This keeps URDF joint count/limits identical to the real robot.
"""
import sys, json
from pathlib import Path
import numpy as np
import mujoco
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
XML = HERE / "m20_description" / "mjcf" / "M20.xml"
MESH_REL = "package://m20_description/meshes/"
OUT = HERE / "m20_description" / "urdf" / "m20.urdf"

def fmt(a):
    return " ".join(f"{x:.6g}" for x in a)

def quat2rpy(q):
    w, x, y, z = q
    r = np.arctan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
    p = np.arcsin(np.clip(2*(w*y - z*x), -1, 1))
    yw = np.arctan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
    return np.array([r, p, yw])

def main():
    m = mujoco.MjModel.from_xml_path(str(XML))
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # name lookups
    bname = {i: mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, i) or f"body{i}" for i in range(m.nbody)}
    gname = {i: (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or f"geom{i}") for i in range(m.ngeom)}

    # body -> parent body and joint
    body_joint = {}
    for j in range(m.njnt):
        if m.jnt_type[j] == mujoco.mjtJoint.mjJNT_FREE:
            continue
        body_joint[m.jnt_bodyid[j]] = j

    lines = ['<?xml version="1.0"?>', '<robot name="m20">']
    lines.append(f'  <material name="grey"><color rgba="0.7 0.7 0.7 1"/></material>')

    for b in range(1, m.nbody):     # skip world
        nm = bname[b]
        # parent chain
        parent = m.body_parentid[b]
        pnm = "world" if parent == 0 else bname[parent]
        # inertial
        mass = m.body_mass[b]
        ipos = m.body_ipos[b]
        iquat = m.body_iquat[b]
        diag = m.body_inertia[b]
        lines.append(f'  <link name="{nm}">')
        lines.append(f'    <inertial>')
        lines.append(f'      <origin xyz="{fmt(ipos)}" rpy="0 0 0"/>')
        lines.append(f'      <mass value="{mass:.6g}"/>')
        lines.append(f'      <inertia ixx="{diag[0]:.6g}" iyy="{diag[1]:.6g}" izz="{diag[2]:.6g}" ixy="0" ixz="0" iyz="0"/>')
        lines.append(f'    </inertial>')
        # geoms of this body
        for g in range(m.ngeom):
            if m.geom_bodyid[g] != b:
                continue
            gpos = m.geom_pos[g]; gquat = m.geom_quat[g]
            if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
                meshname = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_MESH, m.geom_dataid[g])
                if meshname and meshname.endswith(".STL"):
                    lines.append(f'    <visual>')
                    lines.append(f'      <origin xyz="{fmt(gpos)}" rpy="0 0 0"/>')
                    lines.append(f'      <geometry><mesh filename="{MESH_REL}{meshname}"/></geometry>')
                    lines.append(f'      <material name="grey"/>')
                    lines.append(f'    </visual>')
            elif m.geom_type[g] in (mujoco.mjtGeom.mjGEOM_BOX, mujoco.mjtGeom.mjGEOM_CYLINDER, mujoco.mjtGeom.mjGEOM_SPHERE):
                s = m.geom_size[g]
                if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_BOX:
                    geo = f'<box size="{fmt(s*2)}"/>'
                elif m.geom_type[g] == mujoco.mjtGeom.mjGEOM_CYLINDER:
                    geo = f'<cylinder radius="{s[0]:.6g}" length="{2*s[1]:.6g}"/>'
                else:
                    geo = f'<sphere radius="{s[0]:.6g}"/>'
                lines.append(f'    <collision>')
                lines.append(f'      <origin xyz="{fmt(gpos)}" rpy="0 0 0"/>')
                lines.append(f'      <geometry>{geo}</geometry>')
                lines.append(f'    </collision>')
        lines.append(f'  </link>')

        # joint connecting to parent
        if b in body_joint:
            j = body_joint[b]
            jname = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j)
            # joint origin = body position/orientation in the parent body frame
            bpos = m.body_pos[b]
            bquat = m.body_quat[b]
            lo, hi = m.jnt_range[j]
            has_lim = bool(m.jnt_limited[j])
            jtype = "revolute" if m.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE else "prismatic"
            lines.append(f'  <joint name="{jname}" type="{jtype}">')
            lines.append(f'    <parent link="{pnm}"/><child link="{nm}"/>')
            lines.append(f'    <origin xyz="{fmt(bpos)}" rpy="{fmt(quat2rpy(bquat))}"/>')
            lines.append(f'    <axis xyz="{fmt(m.jnt_axis[j])}"/>')
            if has_lim and not (lo == 0 and hi == 0):
                lines.append(f'    <limit lower="{lo:.6g}" upper="{hi:.6g}" effort="{abs(m.jnt_actfrcrange[j][1]):.6g}" velocity="45"/>')
            else:
                lines.append(f'    <limit lower="-1e9" upper="1e9" effort="{abs(m.jnt_actfrcrange[j][1]):.6g}" velocity="100"/>')
            lines.append(f'  </joint>')

    lines.append('</robot>')
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT}  ({len(lines)} lines)")
    # report joint count
    print(f"links={m.nbody-1} actuated_joints={m.nu}")

main()
