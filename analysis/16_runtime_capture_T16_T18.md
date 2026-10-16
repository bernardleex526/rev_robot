# 16 · T16/T17/T18 运行时采集报告（M2）

安全前提：**CP-1 已授权**（`runtime/safety_checklist_CP1.md`）。全部动作为**被动只读**，抓包经 ssh 直传本地，未写狗盘。

## T16 · 上层通信抓包（手柄/App 链路）

| 项 | 结果 |
| --- | --- |
| 采集 | `captures/app_interhost.pcap`（45MB / 149,352 帧 / 90s） |
| 判定 | 手柄/App 未连接，**无 12121/UDP 与 0xEB90EB90 JSON 流量**（符合 CP-1 “App 未连接”） |
| 结论 | 协议**已从源码级还原**（`04_protocols.md`：手柄 `0x55 0x66` + CRC16 @ :12121；App `0xEB90EB90` 16B 头 + JSON `PatrolDevice{Items,Type,Command}`）；真实触发流量需用户持手柄/App 操作（下一会话可补） |

## T17 · 底层总线嗅探

| 检查 | 结果 |
| --- | --- |
| SocketCAN | **不存在** `can0/can1`（`ip -br link show type can` 空） |
| `/dev/can*` | 不存在 |
| eth1 原始帧 | 8s 抓包仅见 DDS 组播（`10.21.32.103.* > 239.255.0.1:7400`），**无 EtherCAT 原始以太网帧** |
| 网卡驱动 | eth0/eth1 = `st_gmac`（ST 千兆 MAC），eth2 = `cdc_ether`（USB） |
| 结论 | `ecan-master` 的电机总线流量**未以可旁路嗅探的形式暴露**在主机网卡上（疑经内核网络栈/专用下发路径或由 MCU 直接持有）。**只读手段无法采集**；若需总线级数据，属 L3（需 SWD/硬件探针），按计划推迟。 |

## T18 · 机间通信抓包（主机 A↔B↔C）

| 项 | 结果 |
| --- | --- |
| 采集 | `captures/interhost_full.pcap`（18.5MB / 11,219 帧 / 40s） |
| 协议 | **RTPS 2.3（Fast DDS，vendorId 0x0f01）**，UDP 7400–7460，domain 0 |
| 载荷 | 已解析 CDR 体，见 `15_protocol_decoding_T20.md`；`frame_id` 单调、时间戳 `sec=1/nsec=0`、`+8` 步长 float 数组 |
| 写入者 | 69 个（A/B/C 三机 + loopback），高频族 = 312B 本体状态、404B 指令族 |
| 结论 | 机间通信**可完整旁路采集并可解码** |

## 产物清单

```
captures/app_interhost.pcap     45MB  90s 全链路（排除雷达/ssh）
captures/interhost_full.pcap    18.5MB 40s RTPS 业务流
decoders/drdds_decoder.py              RTPS+CDR 解码（已验证）
decoders/rtps_drdds_decoder.py         统计视图
decoders/drdds_joints_decoder.py       JointsData 解码（待语义锁定）
decoders/drdds_imu_decoder.py          ImuData 解码（待语义锁定）
decoders/drdds_cdr_sizes.txt           drdds 各消息 CDR 尺寸表
```

## T19 · 建图/导航数据（按用户决定：用机上 rob_bag 替代）

| 项 | 结果 |
| --- | --- |
| 位置 | `/var/opt/robot/data/rob_bag/*.tar.bz2`（12GB，最大 4.26GB / 20260814） |
| 用途 | 替代现场 50m 跑图；供 T24（状态估计）/T25（建图 ATE）/T30（管线复现）离线回放 |
| 现场动作 | **未执行**（无跑图、无站立/行走），故无姿态风险 |

## 未决项

- T16 的真实按键/App 流量（`R2` 阻尼等不改姿态动作）待用户在场时补采。
- T17 的总线级数据非只读可行，按计划归入 L3 推迟。
