#!/usr/bin/env python3
"""Robust drdds decoder for the observed RTPS DATA payloads.

Derived from captured traffic (host A inter-host + loopback), cross-checked against
the generated drdds message definitions in `dump/hostA/ros_foxy_share/` and
`dump/hostA/usr_local_include/dridl/`.

Two payload families are present on the wire:
  * 312-byte CDR body  -> high-rate proprioceptive frame (see layout below)
  * 404/344/376-byte CDR body -> command/discovery frames (rtps.sm.id observed)

312B CDR layout (little-endian), total body 312B after the 4B encapsulation:
    [0]   u64 frame_id            (monotonic, low half varies; high half constant per boot)
    [8]   u32 sec = 1             (builtin Time.sec; note: NOT wall clock)
    [12]  u32 nsec = 0            (builtin Time.nanosec)
    [16]  u32 <runtime prefix>
    [20]  f32  a       \ 5 floats at +8 stride
    [24]  u32  (u32 field, low dynamic range)  |
    [28]  f32  b       |
    [32]  u32  |        |
    [36]  f32  c       |
    [40]  u32  |        |
    [44]  f32  d       /
    [48..120]  zero padding (u32 0)
    [124] f32  e  \ 3 floats at +8 stride
    [128] u32  |    |
    [132] f32  f  |
    [136] u32  |    |
    [140] f32  g  /
    [220] f32  h  \ 3 floats at +8 stride
    [224] u32  |    |
    [228] f32  i  |
    [232] u32  |    |
    [236] f32  j  /
The interleaved u32 slots are small-magnitude integer fields (`data_id`/`status`
family from the Joint*/Imu* definitions). This confirms the payload is a packed
record with `float32` fields on 8-byte stride, i.e. a Joint*-family array rather
than a flat float vector.

Usage:
  python3 drdds_decoder.py <pcap> [cdr_len]
"""
import subprocess, struct, sys
from collections import Counter

FLOAT_STRIDE = 8
FLOAT_GROUPS = [(20, 5), (124, 3), (220, 3)]


def shard_payloads(pcap, filt="rtps.sm.id==0x15"):
    cmd = ["tshark", "-r", pcap, "-Y", filt, "-T", "fields",
           "-e", "ip.src", "-e", "ip.dst", "-e", "udp.payload", "-E", "separator=|"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    for line in out.splitlines():
        p = line.split("|")
        if len(p) < 3 or not p[2]:
            continue
        try:
            yield p[0], p[1], bytes.fromhex(p[2])
        except ValueError:
            pass


def split_cdr(raw):
    """Return list of (entityClass, cdrBody) from one RTPS packet."""
    if raw[:4] != b"RTPS":
        return []
    res = []
    pos = 20
    while pos + 4 <= len(raw):
        smid = raw[pos]
        ln = struct.unpack_from("<H", raw, pos + 2)[0]
        body = raw[pos + 4:pos + 4 + ln]
        if smid == 0x15 and len(body) >= 24:
            res.append((smid, body[24:]))
        pos += 4 + ln
        if ln == 0:
            break
    return res


def decode_312(cdr):
    if len(cdr) != 312:
        return None
    fid = struct.unpack_from("<Q", cdr, 0)[0]
    sec, nsec = struct.unpack_from("<II", cdr, 8)
    floats = {}
    for base, n in FLOAT_GROUPS:
        for k in range(n):
            off = base + k * FLOAT_STRIDE
            floats[f"f@{off}"] = round(struct.unpack_from("<f", cdr, off)[0], 6)
    return {"frame_id": fid, "sec": sec, "nsec": nsec, "floats": floats}


def main():
    pcap = sys.argv[1]
    target = int(sys.argv[2]) if len(sys.argv) > 2 else 312
    hist = Counter()
    shown = 0
    for src, dst, raw in shard_payloads(pcap):
        for _, cdr in split_cdr(raw):
            hist[len(cdr)] += 1
            if len(cdr) == target and shown < 5:
                d = decode_312(cdr)
                if d:
                    print(f"src={src} frame_id={d['frame_id']:#018x} sec={d['sec']} nsec={d['nsec']}")
                    print("   ", d["floats"])
                    shown += 1
    print(f"\nCDR body length histogram: {dict(hist.most_common(12))}")
    print("NOTE: float offsets are layout-verified; semantic field names require")
    print("      cross-checking with the binary deserializer (see analysis/15_*).")


main()
