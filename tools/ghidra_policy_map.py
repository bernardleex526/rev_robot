"""Map each embedded policy symbol to the runner constructor that references it."""
import os

import pyghidra

BIN = "/home/lee/rea/bin/rl_deploy"
OUT = "/home/lee/rea/notes/ghidra_policy_map.txt"
POLICIES = {
    "policy_policy_m20_backknee6": 0x287438,
    "policy_policy_m20_rough_6": 0x379C68,
    "policy_policy_m20_50": 0x46C498,
    "policy_policy_m20_38": 0x55ECC8,
    "policy_policy_ca9bplatform": 0x6514F8,
    "policy_policy_m20_5": 0x744460,
    "policy_m20_forward_policy_2": 0x836C90,
    "policy_m20_sixaxis_stand": 0xA32B00,
    "policy_m20_hmap_motion_v0_2": 0xC38A40,
    "policy_m20_navi_charge_v3_29": 0xFDBAF0,
    "policy_m20_navi_flat_v4_2": 0x10D6428,
    "policy_m20_navi_stair_v7_0_himloco": 0x11CA160,
    "policy_m20_finetune_stand_15kg": 0x12BCC98,
    "policy_m20_flat_v1_4": 0x14C2BD8,
    "policy_m20_finetune_forward": 0x15BEB40,
}
BASE = 0x100000


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fh = open(OUT, "w")

    def log(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        fh.write(s + "\n")
        fh.flush()

    with pyghidra.open_program(BIN) as api:
        program = api.getCurrentProgram()
        fm = program.getFunctionManager()
        refmgr = program.getReferenceManager()
        af = program.getAddressFactory()

        for name, vaddr in POLICIES.items():
            addr = af.getDefaultAddressSpace().getAddress(vaddr + BASE)
            fns = set()
            for r in refmgr.getReferencesTo(addr):
                fn = fm.getFunctionContaining(r.getFromAddress())
                fns.add(fn.getName() if fn else "(none)")
            # also try raw address (some symbols may be unreached by analysis)
            log("%-40s @ 0x%x -> %s" % (name, vaddr, sorted(fns)))

    fh.close()
    print("WROTE", OUT)


main()
