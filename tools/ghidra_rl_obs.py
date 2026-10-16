"""Decompile the observation builder and a policy runner from rl_deploy (has DWARF)."""
import os

import pyghidra

BIN = "/home/lee/rea/bin/rl_deploy"
OUT = "/home/lee/rea/notes/ghidra_updatecmd.txt"
TARGETS = [
    ("M20FinetuneStandRunner::updateCommand", 0x184F9C + 0x100000),
    ("M20ExtrePolicyRunner::updateCommand", 0x17C888 + 0x100000),
    ("M20SixAxisStandRunner::updateCommand", 0x1982A0 + 0x100000),
]


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
        from ghidra.app.decompiler import DecompInterface
        from ghidra.util.task import ConsoleTaskMonitor
        from ghidra.program.model.address import GenericAddress

        fm = program.getFunctionManager()
        af = program.getAddressFactory()
        dec = DecompInterface()
        dec.openProgram(program)
        mon = ConsoleTaskMonitor()

        for label, addr in TARGETS:
            a = af.getDefaultAddressSpace().getAddress(addr)
            f = fm.getFunctionContaining(a)
            log("\n" + "=" * 72)
            log("===== %s  (expected @ 0x%x)" % (label, addr))
            if f is None:
                log("  (no function at that address)")
                continue
            log("  actual: %s @ %s" % (f.getName(), f.getEntryPoint()))
            log("=" * 72)
            try:
                res = dec.decompileFunction(f, 300, mon)
                if res and res.decompileCompleted():
                    log(res.getDecompiledFunction().getC())
                else:
                    log("(decompile failed)")
            except Exception as e:
                log("(error: %s)" % e)

    fh.close()
    print("WROTE", OUT)


main()
