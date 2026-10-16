#!/usr/bin/env python3
"""Extract enum definitions from DWARF debug info of a target ELF."""
import sys
from elftools.elf.elffile import ELFFile

path = sys.argv[1]
wanted = sys.argv[2].split(",") if len(sys.argv) > 2 else None

f = open(path, "rb")
elf = ELFFile(f)
if not elf.has_dwarf_info():
    sys.exit("no DWARF")
dwarf = elf.get_dwarf_info()

for cu in dwarf.iter_CUs():
    top = cu.get_top_DIE()
    for die in top.iter_children() if hasattr(top, "iter_children") else []:
        pass

def walk(die, depth=0):
    try:
        tag = die.tag
    except Exception:
        return
    if tag == "DW_TAG_enumeration_type":
        try:
            name = die.attributes.get("DW_AT_name")
            name = name.value.decode() if name else "?"
        except Exception:
            name = "?"
        if wanted and not any(w.lower() in name.lower() for w in wanted):
            return
        print(f"enum {name}")
        for child in die.iter_children():
            if child.tag == "DW_TAG_enumerator":
                n = child.attributes.get("DW_AT_name")
                v = child.attributes.get("DW_AT_const_value")
                try:
                    n = n.value.decode() if n else "?"
                except Exception:
                    pass
                v = v.value if v else "?"
                print(f"   {n} = {v}")
    for child in die.iter_children():
        walk(child, depth + 1)

for cu in dwarf.iter_CUs():
    walk(cu.get_top_DIE())
