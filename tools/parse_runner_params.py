#!/usr/bin/env python3
"""Parse the decompiled runner constructors to recover per-runner policy parameters."""
import re, json, struct
from pathlib import Path

SRC = Path("/home/lee/rea/notes/ghidra_rl_allctors.txt")
OUT = Path("/home/lee/rea/sim/runner_params.json")

LOCAL_NUM = re.compile(r"^(\s*)local_([0-9a-f]+)\S* = (-?[0-9.]+|0x[0-9a-fA-F]+);")


def hexf(h):
    return struct.unpack("<f", struct.pack("<I", int(h, 16)))[0]


def num(s):
    return round(hexf(s[2:]), 6) if s.startswith("0x") else float(s)


def split_sections(text):
    parts = re.split(r"^=====\s+(\S+)\s+\(expected", text, flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def extract_vec(sec, field):
    lines = sec.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if field in ln and "&local_" in ln:
            start = i
            break
    if start is None:
        for i, ln in enumerate(lines):
            if field in ln:
                start = i
                break
    if start is None:
        return None
    vals = []
    for j in range(start - 1, -1, -1):
        m = LOCAL_NUM.search(lines[j])
        if m:
            vals.append(num(m.group(3)))
            break
    j = start + 1
    while j < len(lines) and len(vals) < 40:
        ln = lines[j]
        if "~CommaInitializer" in ln:
            break
        m = LOCAL_NUM.search(ln)
        if m:
            vals.append(num(m.group(3)))
        j += 1
    return vals


def main():
    text = SRC.read_text()
    secs = split_sections(text)
    res = {}
    for name, sec in secs.items():
        d = {}
        for m in re.finditer(r"\.([a-z_]+_) = (-?[0-9.]+);", sec):
            d[m.group(1)] = float(m.group(2))
        d["dof_pos_default"] = extract_vec(sec, "dof_pos_default_,")
        d["dof_pos_default_trans"] = extract_vec(sec, "dof_pos_default_trans,")
        d["max_cmd_vel"] = extract_vec(sec, "max_cmd_vel_,")
        d["kp"] = extract_vec(sec, "kp_,")
        d["kd"] = extract_vec(sec, "kd_,")
        res[name] = d
    OUT.write_text(json.dumps(res, indent=1))
    for n, d in res.items():
        print(f"\n== {n}")
        print("   scales:", {k: v for k, v in d.items() if k.endswith('_')})
        print("   n_default:", len(d["dof_pos_default"]) if d["dof_pos_default"] else None,
              d["dof_pos_default"])
        print("   n_trans:", len(d["dof_pos_default_trans"]) if d["dof_pos_default_trans"] else None,
              d["dof_pos_default_trans"])
    print("\nWROTE", OUT)


main()
