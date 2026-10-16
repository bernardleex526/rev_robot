"""Ghidra headless analysis of lio_ddsnode: locate LiDAR-IMU extrinsic handling."""
import os

import pyghidra

BIN = "/home/lee/rea/bin/lio_ddsnode"
OUT = "/home/lee/rea/notes/ghidra_lio_extrinsic.txt"
NEEDLES = [b"extrinsic_B_I", b"extrinsic_B_L", b"extrinsic_est_en"]


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

        fm = program.getFunctionManager()
        refmgr = program.getReferenceManager()
        mem = program.getMemory()
        mon = ConsoleTaskMonitor()

        addrs = []
        for needle in NEEDLES:
            start = mem.getMinAddress()
            while True:
                a = mem.findBytes(start, needle, None, True, mon)
                if a is None:
                    break
                addrs.append((needle.decode(), a))
                start = a.add(1)

        log("=== string hits (%d) ===" % len(addrs))
        for name, a in addrs:
            log("  %-20s @ %s" % (name, a))

        funcs = {}
        log("\n=== cross references ===")
        for name, a in addrs:
            refs = list(refmgr.getReferencesTo(a))
            if not refs:
                log("  '%s' @ %s : (no xref to exact address)" % (name, a))
            for r in refs:
                frm = r.getFromAddress()
                fn = fm.getFunctionContaining(frm)
                log("  '%s' <- %s in %s" % (name, frm, fn.getName() if fn else "(none)"))
                if fn is not None:
                    funcs[fn.getEntryPoint().toString()] = fn

        log("\n=== functions to decompile: %d ===" % len(funcs))
        dec = DecompInterface()
        dec.openProgram(program)
        for key in sorted(funcs):
            fn = funcs[key]
            log("\n===== %s @ %s =====" % (fn.getName(), key))
            try:
                res = dec.decompileFunction(fn, 120, mon)
                if res and res.decompileCompleted():
                    log(res.getDecompiledFunction().getC())
                else:
                    log("(decompile failed)")
            except Exception as e:
                log("(error: %s)" % e)

    fh.close()
    print("WROTE", OUT)


main()
