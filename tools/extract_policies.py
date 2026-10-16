#!/usr/bin/env python3
"""Extract embedded policy blobs (__policy_*) from the rl_deploy ELF and parse as ONNX."""
import sys, os, json
from elftools.elf.elffile import ELFFile
from onnx import ModelProto

elf_path = sys.argv[1]
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)

f = open(elf_path, "rb")
elf = ELFFile(f)
# vaddr -> file offset
segs = []
for ph in elf.iter_segments():
    if ph["p_type"] in ("PT_LOAD", "PT_NOTE"):
        segs.append((ph["p_vaddr"], ph["p_filesz"], ph["p_offset"]))

def v2o(vaddr):
    for va, sz, off in segs:
        if va <= vaddr < va + sz:
            return off + (vaddr - va)
    return None

symtab = elf.get_section_by_name(".symtab")
report = []
count = 0
for sym in symtab.iter_symbols():
    name = sym.name
    if "__policy" not in name:
        continue
    vaddr = sym["st_value"]
    size = sym["st_size"]
    off = v2o(vaddr)
    if off is None or size == 0:
        continue
    f.seek(off)
    data = f.read(size)
    status = "unparsed"
    info = {}
    try:
        m = ModelProto()
        m.ParseFromString(data)
        if len(m.graph.node) > 0:
            status = "onnx-ok"
            info = {
                "inputs": [(i.name, [d.dim_value for d in i.type.tensor_type.shape.dim]) for i in m.graph.input],
                "outputs": [(o.name, [d.dim_value for d in o.type.tensor_type.shape.dim]) for o in m.graph.output],
                "nodes": len(m.graph.node),
                "initializers": [(t.name, list(t.dims)) for t in m.graph.initializer],
                "opset": [(o.domain, o.version) for o in m.opset_import],
                "producer": (m.producer_name, m.producer_version),
            }
    except Exception as e:
        info = {"error": str(e)[:120]}
    out = os.path.join(outdir, name.strip("_") + ".onnx")
    if status == "onnx-ok":
        open(out, "wb").write(data)
        count += 1
    report.append({"symbol": name, "vaddr": hex(vaddr), "size": size, "status": status, "file": out if status == "onnx-ok" else None, "info": info})

json.dump(report, open(os.path.join(outdir, "policies_report.json"), "w"), indent=1, ensure_ascii=False)
print(f"extracted {count} ONNX policies")
for r in report:
    print(f"{r['symbol']:45s} size={r['size']:>9d} {r['status']:9s} {r['info'].get('inputs')} -> {r['info'].get('outputs')} nodes={r['info'].get('nodes')}")
