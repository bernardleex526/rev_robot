#!/usr/bin/env python3
"""Minimal RTPS 2.x submessage parser: extract DATA payloads from a UDP pcap.

Reads the pcap via tshark (`-T fields -e udp.payload`), parses the RTPS header and
submessages, and returns (writerEntityId, seq, payloadHex) records.
Only the parts needed for drdds payload extraction are implemented.
"""
import subprocess, sys, struct, json
from collections import Counter, defaultdict

def run_tshark(pcap, bpf="rtps"):
    cmd = ["tshark", "-r", pcap, "-Y", bpf, "-T", "fields",
           "-e", "ip.src", "-e", "ip.dst", "-e", "udp.srcport", "-e", "udp.dstport",
           "-e", "udp.payload", "-E", "separator=|"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.split("|")
        if len(parts) < 5 or not parts[4]:
            continue
        try:
            yield parts[0], parts[1], int(parts[2]), int(parts[3]), bytes.fromhex(parts[4])
        except ValueError:
            continue

def parse_rtps(buf):
    if len(buf) < 20 or buf[0:4] != b"RTPS":
        return None
    ver = (buf[4], buf[5])
    vendor = buf[6:8].hex()
    guid = buf[8:20]
    pos = 20
    msgs = []
    while pos + 4 <= len(buf):
        smid = buf[pos]; flags = buf[pos+1]
        ln = struct.unpack_from("<H", buf, pos+2)[0]
        body = buf[pos+4:pos+4+ln]
        msgs.append((smid, flags, body))
        pos += 4 + ln
        if ln == 0:
            break
    return {"version": ver, "vendor": vendor, "guid": guid, "msgs": msgs}

def extract_data(msgs):
    """Return list of (writerEntityId, seq, payload) for DATA submessages."""
    res = []
    for smid, flags, body in msgs:
        # DATA (0x15) and DATA_FRAG (0x16) — handle 0x15 only
        if smid != 0x15:
            continue
        if len(body) < 24:
            continue
        endian = "<" if (flags & 0x01) else ">"
        extraFlags, octetsToInlineQos = struct.unpack_from(endian + "HH", body, 0)
        readerEid = body[4:8]
        writerEid = body[8:12]
        # SeqNum follows when inlineQos is not present in the DATA
        inline_qos = bool(flags & 0x02)
        p = 12
        if inline_qos:
            # skip inline QoS parameters until sentinel
            qos_start = 12 + octetsToInlineQos - 16 if octetsToInlineQos >= 16 else 12
            q = 12
            while q + 4 <= len(body):
                pid, plen = struct.unpack_from(endian + "HH", body, q)
                q += 4 + ((plen + 3) // 4) * 4
                if pid == 0x0001:  # PID_SENTINEL
                    break
            p = q
        sn_high, sn_low = struct.unpack_from(endian + "ii", body, 12)
        seq = (sn_high << 32) | (sn_low & 0xFFFFFFFF)
        payload_off = 12 + 8  # after SeqNum
        if inline_qos:
            payload_off = p
        payload = body[payload_off:]
        res.append((writerEid.hex(), seq, payload))
    return res

def main():
    pcap = sys.argv[1]
    recs = []
    n = 0
    for src, dst, sp, dp, buf in run_tshark(pcap):
        n += 1
        r = parse_rtps(buf)
        if not r:
            continue
        for weid, seq, pl in extract_data(r["msgs"]):
            recs.append({"src": src, "dst": dst, "sport": sp, "dport": dp,
                         "guid": r["guid"].hex(), "weid": weid, "seq": seq,
                         "len": len(pl), "payload": pl})
    print(f"packets={n} data_msgs={len(recs)}")
    c = Counter(r["len"] for r in recs)
    print("payload length histogram (top 25):")
    for ln, cnt in c.most_common(25):
        print(f"  len={ln:6d}  count={cnt}")
    byw = defaultdict(list)
    for r in recs:
        byw[(r["src"], r["guid"], r["weid"])].append(r)
    print(f"\nwriters: {len(byw)}")
    for k, v in sorted(byw.items(), key=lambda kv: -len(kv[1]))[:20]:
        lens = Counter(x["len"] for x in v)
        print(f"  {k} n={len(v)} lens={dict(lens.most_common(4))} first_payload={v[0]['payload'][:24].hex()}")
    json.dump([{**{k: r[k] for k in r if k != 'payload'}, "payload_hex": r["payload"].hex()} for r in recs[:400]],
              open(sys.argv[2] if len(sys.argv) > 2 else "/dev/stdout", "w"), indent=1) if len(sys.argv) > 2 else None

main()
