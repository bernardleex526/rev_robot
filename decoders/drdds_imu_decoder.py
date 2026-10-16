#!/usr/bin/env python3
"""Decode drdds ImuData (CDR) from captured RTPS DATA payloads.

drdds/msg/ImuData { MetaType header; ImuDataValue data; }
  MetaType{ uint64 frame_id; Time{int32 sec; uint32 nanosec} }              -> 16B
  NOTE: this data type is serialized with a fixed prefix (id/stamp) as seen
  on the wire, then 9 little-endian float32.
Observed CDR layout (little-endian), total 312B for the high-rate body:
   [0] frame_id  (u64)      e.g. 0x2ffc593766778a34
   [8]  sec      (u32)  = 1
   [12] nsec     (u32)  = 0
   [16] <runtime prefix word>
   [20] roll, [24] pitch, ... consecutive float32 every 4B
"""
import subprocess, struct, sys, json
from collections import Counter

def payloads(pcap, filt="rtps.sm.id==0x15"):
    cmd = ["tshark", "-r", pcap, "-Y", filt, "-T", "fields",
           "-e", "ip.src", "-e", "ip.dst", "-e", "udp.payload", "-E", "separator=|"]
    for line in subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines():
        p = line.split("|")
        if len(p) < 3 or not p[2]:
            continue
        try:
            yield p[0], p[1], bytes.fromhex(p[2])
        except ValueError:
            pass

def data_cdr(raw):
    if raw[:4] != b"RTPS":
        return None
    pos = 20
    while pos + 4 <= len(raw):
        smid = raw[pos]; ln = struct.unpack_from("<H", raw, pos + 2)[0]
        body = raw[pos + 4:pos + 4 + ln]
        if smid == 0x15:
            return body[24:]
        pos += 4 + ln
        if ln == 0:
            break
    return None

def main():
    pcap = sys.argv[1]
    L = int(sys.argv[2]) if len(sys.argv) > 2 else 312
    f0 = int(sys.argv[3]) if len(sys.argv) > 3 else 20     # first float offset
    nf = int(sys.argv[4]) if len(sys.argv) > 4 else 9      # number of floats
    labels = ["roll","pitch","yaw","omega_x","omega_y","omega_z","acc_x","acc_y","acc_z"]
    shown = 0; cnt = 0
    for src, dst, raw in payloads(pcap):
        cdr = data_cdr(raw)
        if cdr is None or len(cdr) != L:
            continue
        cnt += 1
        if shown < 4 and src == "127.0.0.1":
            fid = struct.unpack_from("<Q", cdr, 0)[0]
            vals = struct.unpack_from("<%df" % nf, cdr, f0)
            print(f"frame_id={fid:#x} src={src}")
            for lb, v in zip(labels, vals):
                print(f"   {lb:8s} = {v: .5f}")
            shown += 1
    print(f"decoded {cnt} ImuData-like payloads (cdr={L}B)")

main()
