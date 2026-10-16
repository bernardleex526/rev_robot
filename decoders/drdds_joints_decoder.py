#!/usr/bin/env python3
"""Decode drdds JointsData (CDR) from captured RTPS DATA payloads.

drdds/msg/JointsData { MetaType header; JointsDataValue data; }
  MetaType    { uint64 frame_id; builtin_interfaces/Time stamp{int32 sec; uint32 nanosec} }  -> 16B
  JointData   { char[4] name; uint16 data_id; uint16 status_word;
                float32 position, torque, velocity, motion_temp, driver_temp }              -> 32B * 16 = 512B
Total CDR body = 16 + 512 = 528 (observed 312 -> encoder variant / different topic shape)
"""
import subprocess, struct, sys
from collections import Counter

def payloads(pcap, filt="rtps.sm.id==0x15"):
    cmd = ["tshark", "-r", pcap, "-Y", filt, "-T", "fields", "-e", "ip.src", "-e", "udp.payload", "-E", "separator=|"]
    for line in subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines():
        p = line.split("|")
        if len(p) < 2 or not p[1]:
            continue
        try:
            yield p[0], bytes.fromhex(p[1])
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
            return body[24:]        # skip RTPS DATA hdr + 4B CDR encapsulation
        pos += 4 + ln
        if ln == 0:
            break
    return None

def meta(cdr):
    fid = struct.unpack_from("<Q", cdr, 0)[0]
    sec, nsec = struct.unpack_from("<iI", cdr, 8)
    return fid, sec, nsec

def joint(b, off):
    name = b[off:off+4].decode("latin1", "replace")
    did, st = struct.unpack_from("<HH", b, off + 4)
    p, v, t, mt, dt = struct.unpack_from("<fffff", b, off + 8)
    return dict(name=name, data_id=did, status=st,
                pos=round(p, 4), vel=round(v, 4), tau=round(t, 4),
                motor_temp=round(mt, 1), driver_temp=round(dt, 1))

def main():
    pcap = sys.argv[1]
    target_len = int(sys.argv[2]) if len(sys.argv) > 2 else 312
    hist = Counter(); shown = 0
    for src, raw in payloads(pcap):
        cdr = data_cdr(raw)
        if cdr is None or len(cdr) != target_len:
            continue
        hist[len(cdr)] += 1
        if shown < 3:
            fid, sec, nsec = meta(cdr)
            print(f"--- from {src} frame_id={fid:#x} stamp={sec}.{nsec:09d} cdr={len(cdr)}B ---")
            for k in range(4):
                off = 16 + k * 32
                if off + 32 <= len(cdr):
                    j = joint(cdr, off)
                    if j["name"].strip("\x00 "):
                        print("   ", j)
            shown += 1
    print("hist:", dict(hist))

main()
