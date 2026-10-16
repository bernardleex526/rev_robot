#!/usr/bin/env python3
"""Decode ROS2 sqlite3 bags recorded by rob_bag (nav_msgs/Odometry, PointCloud2).

Verified CDR layout for nav_msgs/Odometry (little-endian, 4B encapsulation):
  [0]  encap = 00 01 00 00
  [4]  builtin Time { int32 sec; uint32 nanosec }             (wall clock, ns since epoch)
  [12] string frame_id      (uint32 len incl NUL + bytes)
  ...  string child_frame_id
  ...  align to 8, then 13 float64:
         pose.position[3], pose.orientation[4] (x,y,z,w),
         twist.linear[3], twist.angular[3]
  Total observed length = 708 B.
"""
import sqlite3, struct, sys, math, json

def decode_odom(data):
    if len(data) < 40:
        return None
    endian = "<" if data[1] == 0x01 else ">"
    off = 4
    sec, nsec = struct.unpack_from(endian + "iI", data, off); off += 8
    out = {"stamp": sec + nsec * 1e-9, "sec": sec, "nsec": nsec}
    for key in ("frame_id", "child_frame_id", "child"):
        if off + 4 > len(data):
            return None
        ln = struct.unpack_from(endian + "I", data, off)[0]
        if ln == 0 or ln > 256 or off + 4 + ln > len(data):
            break
        out[key if key != "child" else "child_frame_id"] = data[off+4:off+4+ln-1].decode("latin1")
        off += 4 + ln
    # locate 13 consecutive float64 forming a valid quaternion
    for base in range(off, min(off + 32, len(data) - 104)):
        vals = struct.unpack_from(endian + "13d", data, base)
        qn = math.sqrt(sum(v * v for v in vals[3:7]))
        if abs(qn - 1.0) < 0.01 and abs(vals[0]) < 1e5:
            out.update({
                "pos": [round(v, 4) for v in vals[0:3]],
                "quat": [round(v, 4) for v in vals[3:7]],
                "lin": [round(v, 4) for v in vals[7:10]],
                "ang": [round(v, 4) for v in vals[10:13]],
            })
            return out
    return out

def topics(db):
    c = sqlite3.connect(db)
    return {i: (n, t) for i, n, t in c.execute("select id,name,type from topics")}

def main():
    db = sys.argv[1]
    c = sqlite3.connect(db)
    tmap = topics(db)
    for tid, (name, typ) in tmap.items():
        n = c.execute("select count(*) from messages where topic_id=?", (tid,)).fetchone()[0]
        print(f"topic {tid}: {name} [{typ}] messages={n}")
        if "Odometry" not in typ or n == 0:
            continue
        rows = c.execute("select data,timestamp from messages where topic_id=? order by timestamp limit 3", (tid,)).fetchall()
        for data, ts in rows:
            print("   ", decode_odom(data))

if __name__ == "__main__":
    main()
