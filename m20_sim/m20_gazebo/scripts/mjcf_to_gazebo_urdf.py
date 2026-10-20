#!/usr/bin/env python3
"""Generate a Gazebo-ready URDF for the M20 from the official MJCF.

Unlike sim/mjcf_to_urdf.py in the reverse-engineering repo, this keeps visual meshes,
collision primitives, the full rotated inertia tensor, continuous wheel joints,
and adds Gazebo friction/contact parameters and the m20_gazebo plugin.

Usage: python3 mjcf_to_gazebo_urdf.py <M20.xml> <out.urdf> [--mesh-uri package://m20_gazebo/meshes]
"""
import argparse
import math
import xml.etree.ElementTree as ET

import numpy as np


def fvec(s, n=None, default=None):
    if s is None:
        return np.array(default, dtype=float)
    v = np.array([float(x) for x in s.split()], dtype=float)
    return v if n is None else v[:n]


def quat_to_mat(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def mat_to_rpy(R):
    # URDF rpy = fixed-axis XYZ (R = Rz(y) Ry(p) Rx(r))
    sy = math.hypot(R[0, 0], R[1, 0])
    if sy > 1e-9:
        r = math.atan2(R[2, 1], R[2, 2])
        p = math.atan2(-R[2, 0], sy)
        y = math.atan2(R[1, 0], R[0, 0])
    else:
        r = math.atan2(-R[1, 2], R[1, 1])
        p = math.atan2(-R[2, 0], sy)
        y = 0.0
    return r, p, y


def fmt(v):
    return " ".join(f"{x:.9g}" for x in v)


def origin(parent, xyz, rpy=(0, 0, 0)):
    ET.SubElement(parent, "origin", xyz=fmt(xyz), rpy=fmt(rpy))


def add_inertial(link, inert):
    pos = fvec(inert.get("pos"), 3, [0, 0, 0])
    q = fvec(inert.get("quat"), 4, [1, 0, 0, 0])
    d = fvec(inert.get("diaginertia"), 3)
    R = quat_to_mat(q)
    I = R @ np.diag(d) @ R.T
    el = ET.SubElement(link, "inertial")
    origin(el, pos)
    ET.SubElement(el, "mass", value=f"{float(inert.get('mass')):.9g}")
    ET.SubElement(el, "inertia", ixx=f"{I[0,0]:.9g}", ixy=f"{I[0,1]:.9g}", ixz=f"{I[0,2]:.9g}",
                  iyy=f"{I[1,1]:.9g}", iyz=f"{I[1,2]:.9g}", izz=f"{I[2,2]:.9g}")


def add_geom(link, geom, mesh_files, mesh_uri, idx):
    cls = geom.get("class")
    pos = fvec(geom.get("pos"), 3, [0, 0, 0])
    rpy = mat_to_rpy(quat_to_mat(fvec(geom.get("quat"), 4, [1, 0, 0, 0])))
    gtype = geom.get("type", "sphere")
    if cls == "visual":
        el = ET.SubElement(link, "visual")
        origin(el, pos, rpy)
        g = ET.SubElement(el, "geometry")
        ET.SubElement(g, "mesh", filename=f"{mesh_uri}/{mesh_files[geom.get('mesh')]}")
        mat = ET.SubElement(el, "material", name="m20_grey")
        ET.SubElement(mat, "color", rgba="0.7 0.7 0.7 1")
        return None
    el = ET.SubElement(link, "collision", name=f"{link.get('name')}_collision_{idx}")
    origin(el, pos, rpy)
    g = ET.SubElement(el, "geometry")
    size = fvec(geom.get("size"))
    if gtype == "box":
        ET.SubElement(g, "box", size=fmt(2 * size[:3]))
    elif gtype == "cylinder":
        ET.SubElement(g, "cylinder", radius=f"{size[0]:.9g}", length=f"{2 * size[1]:.9g}")
    elif gtype == "sphere":
        ET.SubElement(g, "sphere", radius=f"{size[0]:.9g}")
    else:
        raise ValueError(f"unsupported collision geom type {gtype}")
    return gtype


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mjcf")
    ap.add_argument("out")
    ap.add_argument("--mesh-uri", default="package://m20_gazebo/meshes")
    ap.add_argument("--no-plugin", action="store_true")
    args = ap.parse_args()

    root = ET.parse(args.mjcf).getroot()
    mesh_files = {m.get("name"): m.get("file") for m in root.iter("mesh")}
    world = root.find("worldbody")
    base = world.find("body")

    robot = ET.Element("robot", name="m20")
    gz_refs = []
    joint_names = []

    def walk(body, parent_name):
        name = body.get("name")
        link = ET.SubElement(robot, "link", name=name)
        inert = body.find("inertial")
        if inert is not None:
            add_inertial(link, inert)
        is_wheel = name.endswith("_wheel")
        for i, geom in enumerate(body.findall("geom")):
            add_geom(link, geom, mesh_files, args.mesh_uri, i)
        gz_refs.append((name, is_wheel))

        if parent_name is not None:
            j = body.find("joint")
            pos = fvec(body.get("pos"), 3, [0, 0, 0])
            rpy = mat_to_rpy(quat_to_mat(fvec(body.get("quat"), 4, [1, 0, 0, 0])))
            jname = j.get("name")
            jtype = "continuous" if j.get("range") is None else "revolute"
            jel = ET.SubElement(robot, "joint", name=jname, type=jtype)
            origin(jel, pos, rpy)
            ET.SubElement(jel, "parent", link=parent_name)
            ET.SubElement(jel, "child", link=name)
            ET.SubElement(jel, "axis", xyz=fmt(fvec(j.get("axis"), 3)))
            frc = fvec(j.get("actuatorfrcrange"), 2)
            lim = {"effort": f"{frc[1]:.9g}", "velocity": "30.0"}
            if jtype == "revolute":
                rng = fvec(j.get("range"), 2)
                lim.update(lower=f"{rng[0]:.9g}", upper=f"{rng[1]:.9g}")
            ET.SubElement(jel, "limit", **lim)
            ET.SubElement(jel, "dynamics", damping="0.0", friction="0.0")
            joint_names.append(jname)

        for child in body.findall("body"):
            walk(child, name)

    # base_link pose comes from the spawn call, not from the MJCF body pos
    walk(base, None)

    # IMU frame (MJCF site imu_site)
    imu = base.find("site[@name='imu_site']")
    if imu is not None:
        ET.SubElement(robot, "link", name="imu_link")
        jel = ET.SubElement(robot, "joint", name="imu_joint", type="fixed")
        origin(jel, fvec(imu.get("pos"), 3))
        ET.SubElement(jel, "parent", link="base_link")
        ET.SubElement(jel, "child", link="imu_link")

    for name, is_wheel in gz_refs:
        ref = ET.SubElement(robot, "gazebo", reference=name)
        ET.SubElement(ref, "mu1").text = "1.0"
        ET.SubElement(ref, "mu2").text = "1.0"
        # stiff contact, roughly matching MJCF solref 0.005
        ET.SubElement(ref, "kp").text = "1e6"
        ET.SubElement(ref, "kd").text = "100"
        ET.SubElement(ref, "minDepth").text = "0.001"
        ET.SubElement(ref, "maxVel").text = "1.0"
        ET.SubElement(ref, "selfCollide").text = "false"
        if is_wheel:
            ET.SubElement(ref, "fdir1").text = "0 1 0"

    if not args.no_plugin:
        g = ET.SubElement(robot, "gazebo")
        p = ET.SubElement(g, "plugin", name="m20_drdds_bridge", filename="libm20_gazebo_bridge.so")
        ET.SubElement(p, "imu_link").text = "base_link"
        ET.SubElement(p, "imu_offset").text = fmt(fvec(imu.get("pos"), 3)) if imu is not None else "0 0 0"
        ET.SubElement(p, "joints").text = " ".join(joint_names)
        ET.SubElement(p, "publish_rate").text = "200"

    ET.indent(robot, space="  ")
    # no XML declaration: spawn_entity.py's lxml parser rejects str input that declares an encoding
    ET.ElementTree(robot).write(args.out, encoding="unicode")
    total = sum(float(b.find("inertial").get("mass")) for b in base.iter("body") if b.find("inertial") is not None)
    print(f"wrote {args.out}: {len(gz_refs)} links, {len(joint_names)} joints, mass {total:.4f} kg")


if __name__ == "__main__":
    main()
