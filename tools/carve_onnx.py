#!/usr/bin/env python3
"""Carve embedded ONNX ModelProto blobs out of the rl_deploy ELF."""
import sys, glob, os
try:
    from onnx import ModelProto
except ImportError:
    sys.exit("onnx not installed")

path = sys.argv[1]
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)
data = open(path, "rb").read()

anchors = []
i = 0
while True:
    i = data.find(b"pytorch", i)
    if i < 0:
        break
    anchors.append(i)
    i += 1
print(f"pytorch anchors: {len(anchors)}")

found = {}
for a in anchors:
    for start in range(max(0, a - 80), a):
        if data[start] != 0x08:
            continue
        for length in (600_000, 1_200_000, 2_000_000, 400_000, 200_000):
            blob = data[start:start + length]
            try:
                m = ModelProto()
                m.ParseFromString(blob)
            except Exception:
                continue
            if len(m.graph.node) == 0:
                continue
            ins = [x.name for x in m.graph.input]
            outs = [x.name for x in m.graph.output]
            if not outs:
                continue
            key = (tuple(ins), tuple(outs), len(m.graph.node))
            if key in found:
                continue
            fname = os.path.join(outdir, f"carved_{start:08x}.onnx")
            open(fname, "wb").write(blob)
            found[key] = (start, fname, ins, outs, len(m.graph.node), len(m.graph.initializer))
            print(f"OK start={start} len<= {length} in={ins} out={outs} nodes={len(m.graph.node)} wit={len(m.graph.initializer)} -> {fname}")
            break

print(f"\nunique models: {len(found)}")
for k, v in found.items():
    print(v)
