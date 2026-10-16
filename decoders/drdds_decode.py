#!/usr/bin/env python3
"""Decode drdds CDR payloads captured from RTPS DATA submessages.

Usage: python3 drdds_decode.py <pcap> [topic_guess]
"""
import subprocess, sys, struct
from collections import Counter, defaultdict

# CDR sizes (body after the 4-byte encapsulation header) from dridl *CdrAux.hpp
SIZES = {}
for line in open("/home/lee/rea/decoders/drdds_cdr_sizes.txt"):
    line = line.strip()
    if "=" in line:
        k, v = line.split("=")
        SIZES[k.strip()] = int(v)

# observed full payload lengths (encap 4 + body) -> candidate type
OBS = {408: "JointsDataCmd(548?)/JointArgs", 316: "JointsData? ", 52: "?", 348: "?", 28: "MetaType",
       36: "Gait/MotionState", 708: "?", 8: "StdMsg", 380: "?", 208: "?", 168: "?", 352: "?", 376: "?", 88: "?", 64: "?", 12: "StdStatus"}


def read_payloads(pcap):
    cmd = ["tshark", "-r", pcap, "-Y", "rtps.sm.id==0x15", "-T", "fields",
           "-e", "ip.src", "-e", "ip.dst", "-e", "udp.payload", "-E", "separator=|"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    for line in out.splitlines():
        p = line.split("|")
        if len(p) < 3 or not p[2]:
            continue
        try:
            yield p[0], p[1], bytes.fromhex(p[2])
        except ValueError:
            continue


def cdr_body(raw):
    """Raw = full UDP payload (RTPS header+submsgs). Find the DATA body."""
    # Reuse the same walk as rtps_drdds_decoder
    if raw[:4] != b"RTPS":
        return None
    pos = 20
    while pos + 4 <= len(raw):
        smid = raw[pos]; flags = raw[pos+1]
        ln = struct.unpack_from("<H", raw, pos+2)[0]
        body = raw[pos+4:pos+4+ln]
        if smid == 0x15 and len(body) >= 20:
            encap = body[20:24] if len(body) > 24 else b""
            payload = body[20:]  # best-effort
            return payload, encap
        pos += 4 + ln
        if ln == 0:
            break
    return None, None


def main():
    pcap = sys.argv[1]
    hist = Counter()
    samples = defaultdict(list)
    for src, dst, raw in read_payloads(pcap):
        body, encap = cdr_body(raw)
        if body is None:
            continue
        L = len(raw)  # total udp payload length is a stable fingerprint
        hist[L] += 1
        if len(samples[L]) < 3:
            samples[L].append((src, dst, raw[-min(len(raw), 80):].hex()))
    print(f"{'udp_payload_len':>16}  {'count':>6}  candidate(CDR full = body+8)")
    for L, c in hist.most_common(25):
        body_len = L - 20 - 8 - 4  # rough: RTPS hdr(20)+DATA hdr(20)? approximation
        print(f"{L:>16}  {c:>6}  body~{body_len}  {samples[L][0][2][:56]}")


main()
