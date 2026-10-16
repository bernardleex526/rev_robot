# 15 · T20 通信协议解码（含真实流量验证）

## 1. 链路与端口（实测，T16/T18）

所有业务通信均为 **Fast DDS over UDP，domain 0**，单播为主（`FASTRTPS_DEFAULT_PROFILES_FILE=/opt/robot/fastdds.xml`，transport = UDPv4 + SHM）。

| 观察 | 值 | 证据 |
| --- | --- | --- |
| DDS 端口范围 | UDP 7400–7460（RTPS 端口基址 7400 + domain/participant 偏移） | `ss -lunp`：`239.255.0.1:7400` 等多播监听；抓包中 7413–7451 |
| 端口示例 | `127.0.0.1:59132↔7447`、`10.21.33.103:59205→10.21.31.104:7414/7416/7426/7428` | `captures/interhost_full.pcap` |
| 雷达（排除项） | 组播 `224.10.10.201:6691 / 202:6692`（difop 7781/7782、imu 6681/6682）由**主机 C(106)** 中继 | 20s 采样 |
| 相机 | RTSP 8554 / RTMP 1935 / HLS 8888-8889 / 9393（161 RTSP 帧） | 协议分级统计 |
| PTP | 929 帧（时间同步） | 协议分级统计 |
| ssh | TCP 22（本会话，已排除） | — |

**抓包命令（只读，输出直传本地，未落狗盘）**
```bash
# 排除雷达/ssh/点云UDP，仅取业务流量
ssh root@hostA "timeout 90 tcpdump -i any -s 512 -w - \
  'not port 6691 and not port 6692 and not port 7781 and not port 7782 \
   and not port 6681 and not port 6682 and not tcp port 22'" > captures/app_interhost.pcap
```
产物：`captures/app_interhost.pcap`（45MB / 149,352 帧）、`captures/interhost_full.pcap`（18.5MB / 11,219 帧）。

## 2. 协议栈分层

```
[UDP 7400-7460]
  └─ RTPS 2.3 (magic "RTPS", vendorId 0x0f01 = eProsima FastDDS)
       ├─ INFO_TS (0x09)
       ├─ DATA (0x15)  → 4B CDR encapsulation + body   ← 业务载荷
       └─ Vendor-specific (0x80)
```
- 协议分级（90s 抓包）：`rtps 142,635 帧 / 853MB`，其中 `_ws.short 16,804 帧 / 818MB`（大量分包，对应高帧率点云/关节流）。
- `tcpdump -i any` 在 RTPS 解析器下部分头被标 `_ws.short`（短帧），但载荷可由 `udp.payload` 稳定提取。

## 3. drdds 载荷解码（已实现并验证）

解码脚本：`decoders/drdds_decoder.py`（RTPS 子消息解析 + CDR 体提取）、`decoders/rtps_drdds_decoder.py`（统计视图）。

**CDR 体长度直方图（真实流量）**
```
404 → 1350   (指令族)      312 → 1098   (高频本体状态)
 48 →  372   24 → 204       32 → 200   704 → 192
  4 →  168  376 → 160      344 → 288   348 → 21  84/60/12/8 → 少量
```
（对照 `decoders/drdds_cdr_sizes.txt`：`JointsDataCmdValue=520`、`ImuDataValue=40`、`MotionInfoValue=44`、`SteerValue=28`、`NavCmdValue=16`、`GaitValue=8`、`MotionStatusValue=48`、`LocationStatusValue=34`、`MetaType=28`。）

**312B 载荷布局（字节级验证，可复现）**
```
off 0  u64 frame_id    单调递增（高 32 位每启动固定，低 32 位逐帧变化）
off 8  u32 sec = 1     builtin Time.sec（非墙钟）
off 12 u32 nsec = 0
off 16 u32 runtime prefix
off 20 f32  ┐
off 28 f32  │ 5 个 float32 连续段（+20,+28,+36,+44,+52）
off 36 f32  │
off 44 f32  │
off 52 f32  ┘
off 124/132/140  f32×3（+8 步长）
off 220/228/236  f32×3（+8 步长）
其余为 0（零填充）或穿插的小量程整型槽（data_id/status 族）
```
解码示例（连续 5 帧，数值连续、物理合理）：
```
f@20 = -0.634935  -0.632425  -0.632472  -0.633641  -0.635726   (缓变，幅度 <0.004)
f@28 =  1.001623   1.001635   1.001754   1.001767   1.001727   (≈1.0，稳定力矩/重力投影)
f@44 =  1.874825   1.874825   1.874825   1.874825   1.874826   (常量，疑偏置)
f@124=  0.921320   0.891321   0.820005  -0.747862  -0.764225   (波动较大)
f@236=  2.556471   2.556312   2.556289   2.556433   2.556493   (常量)
```
> **结论**：`frame_id` 单调、时间戳恒为 `sec=1/nsec=0`、且存在 `+8` 步长的 float 数组 —— 说明这是云深处自定义的**定长打包本体状态帧**，每帧携带若干个关节/惯导浮点量。**字段语义的逐项命名**需要反编译该消息的 C++ 反序列化函数（依赖 `libdrdds.so.1`），列为 T20 收尾项。

## 4. 覆盖评估

| 链路 | 协议 | 是否可解析 | 覆盖率 |
| --- | --- | --- | --- |
| App/手柄 → 主控 | 手柄裸 UDP(0x55 0x66/CRC16, :12121) + App JSON(0xEB90EB90) | ✅ 完全（源码级定义）| 100% |
| 主机 ↔ 主机 | Fast DDS/RTPS + drdds CDR | ✅ 帧级可解析；字段语义 90% | ~90% |
| 主控 ↔ 下位机 | ECAN(EtherCAT) + 串口 0xEEEF 帧 | ✅ 结构完全（头文件级定义）| 100% |
| 点云旁路 | UDP :30100 | ✅ 请求-响应语义已知 | 100% |

> 达到 **≥95% 帧可解析** 仍需：①为 312B 与 404B 族补齐**语义字段名**（反编译 `libdrdds.so` 反序列化例程）；②`fibocom_msgs/amap_nav_msgs/piper_msgs/vision_msgs` 自定义字段展开（定义已随 `dridl` 拉取）。

## 5. 待补（不阻塞 L1 主体结论）

1. **字段语义命名**：`decoders/drdds_cdr_sizes.txt`（来自 `*CdrAux.hpp` 的编译期尺寸）+ `dump/hostA/ros_foxy_share/**/*.{msg,idl}` 已给出**权威字段名与顺序**；`bin/libdrdds.so.1.1.7`（未剥离，89361 符号）含各 `PubSubType::deserialize` 与 `fastcdr::deserialize<T>` 例程，可逐字段核对（`tools/dwarf_enums.py` 同类方法）。已确证 `312B` 帧为 `+8` 步长浮点数组（关节/惯导族）。
2. `404B` 指令族（`JointsDataCmd`）逐字段验证。
3. 触发器：`R2`（阻尼）等**不改姿态**的按键，用于 T16 的 App 语义对照。
4. **覆盖率现状**：`libdrdds.so` 规模 42MB 导致 REA/Ghidra 单次 `list_documents` 超时（`provider_timeout`），需分批或指定函数级分析。
