# 23 · 实机在线核验报告（只读对照）

> 时间：实机 Wi-Fi 已连接（本机 `wlp4s0 = 10.21.41.145/24`，SSH 入口 `user@10.21.41.1`）。
> 方法：三机只读 SSH + 哈希比对 + DDS 图查询 + 5 秒裸捕（tcpdump）。**未写盘、未停服务、未动电机。**

## 0. 核验结论速览

| 类别 | 结论 |
| --- | --- |
| 三机拓扑 / OS / 内核 | ✅ **完全属实** |
| 8 个关键二进制哈希（AOS 3 + NOS 4 + ECAN 固件 1） | ✅ **逐一字节一致** |
| ROS 2 Foxy + Fast DDS 2.14.0 | ✅ 属实 |
| LIO / 导航 / 硬件配置文件逐项取值 | ✅ 属实 |
| DDS 话题（98）/ 服务清单 | ✅ 属实 |
| 15 个内嵌 ONNX 策略 | ✅ 属实 |
| **ECAN 协议性质** | ⚠️ **需修正**：非 EtherCAT，是 CAN-FD over Ethernet |
| **rl_deploy 调度策略** | ⚠️ **需修正**：SCHED_RR（非 SCHED_FIFO） |
| **双雷达驱动** | ✅ **已定案**：`rslidar` 生效，`hsLidar` 空转 |

---

## 1. 主机与系统身份（✅ 属实）

| 主机 | 角色 | 网口 | 结论 |
| --- | --- | --- | --- |
| 10.21.31.103 | AOS | eth2=.31.103 / eth0=.33.103 / eth1=.32.103 / wlan0=10.21.41.1 | ✅ |
| 10.21.31.104 | GOS | eth0=.31.104 | ✅ |
| 10.21.31.106 | NOS | eth1=.31.106 / eth0=.33.106 | ✅ |

- 三机均 `Ubuntu 20.04.6 LTS`、`aarch64`、内核 `5.10.198`；登录用户 `user`（uid=1003，属 sudo 组）。
- 镜像版本：`103_v1.0_v2.0_0728` / `104_…` / `106_…`（与还原的 `v1.0.0.0` 一致）。
- **新增事实**：AOS 还有 `eth1=10.21.32.103`、`p2p0=10.8.13.122/23`（点对点链路），此前未记录。
- **异常**：设备 RTC 未设置，自报时间 `2024-06-24`（本机为 2026-10-15），故实时日志写入 `/var/opt/robot/log/2024_0624/`。

## 2. 二进制哈希比对（✅ 全部字节一致）

这是最强证据：我们做静态分析用的二进制 = 实机当前运行的二进制。

| 二进制 | SHA-256（前 16 位） | 匹配 |
| --- | --- | --- |
| `rl_deploy` | `59aa77a24cf42304` | ✅ |
| `basic_server` | `2faf5921b6772f0a` | ✅ |
| `lio_ddsnode` | `0ea536e612b35387` | ✅ |
| `astar_node`（NOS） | `d81f5b4776507b0f` | ✅ |
| `localPlanner`（NOS） | `811d309e1a45d2f2` | ✅ |
| `localization_ddsnode`（NOS） | `249b81c1ab892528` | ✅ |
| `handler`（NOS） | `f6310a90732a34f5` | ✅ |
| `ecan_V2.0.15_*.bin`（固件） | `91f585442b72e43f` | ✅ |

`rl_deploy`：94,505,688 B、`with debug_info, not stripped`、`.debug_info`/`.symtab` 齐备，FUNC 符号 10,317 个。

## 3. 运行时进程拓扑（✅ 属实）

**AOS(103)**：`rl_deploy`、`basic_server`、`ctrlmcu_node`、`lio_ddsnode`、`height_map_nav`、`yesense`(IMU)、`gps`、`cpu`、`rslidar`、`hsLidar`。
**NOS(106)**：`astar_node`、`localPlanner`、`pcl_pass_grid`、`localization_ddsnode`、`handler`、`charge_manager`、`map_server`。

- 调度/亲和性：`rl_deploy` = **SCHED_RR prio 90**，`taskset -c 4,5`（⚠️ 非 SCHED_FIFO）；`astar_node` = chrt 45、CPU6,7；`localPlanner` = chrt 50、CPU6,7。
- NOS 未运行 `slam_ddsnode`（定位用预载地图 `/var/opt/robot/data/maps/active/occ_grid.yaml`）。

## 4. 配置文件逐项核对（✅ 属实）

- **LIO `params.yaml`**：`input_lidar_topic=/LIDAR/POINTS`、`input_imu_topic=/IMU_YESENSE`、`lidar_type=1`(速腾)、`acc_cov/gyr_cov=0.8`、`b_acc_cov/b_gyr_cov=0.01`、`extrinsic_est_en=false`、`max_iteration=3`、`leaf_size=0.15`、`skip_num=9`、`esti_plane_threshold=0.1`、`lidar_cov=0.001`、`deepest/plane/top_level=2/2/1`、`full_map_save_path=/var/opt/robot/data/maps/active/full_cloud.pcd` —— **全部吻合**。
  - ⚠️ `extrinsic_B_I`/`extrinsic_B_L` 确为**单位阵**（坐实"占位"未知项）。
  - 日志确证 `LIO version: 1.0.13`、`UDP server listening on port 30100`。
- **`config_astar.yaml`**：`weight_a=1.0`、`weight_b=1.3`、`weight_heading=0.8`、`cost_steer=1.0`、`cost_steerchange=0.2`、`cost_gear=2.0`、`cost_backward=1.5`、`cost_reduce=0.85`、`step_size=0.4`、`sample_interval=0.2`、`bodyLength/Width=0.45`、`max_steer=0.9`、`num_steerind=3`、`goalDis=0.5`、`enable_smoothing=true`、`smooth_count=7`、`smooth_degree=3`、`angle_threshold=60` —— **全部吻合**。
- **`localplanner.yaml`**：`maxSpeedX=1.5`、`maxSpeedY=0.6`、`maxTheta=1.0`、`stop_distance=0.7`、`robotLength=0.84`、`robotWidth=0.5`、`weight_goal=1.0`、`weight_yaw=0.5`、`weight_spdy=0.2`、`weight_ob1/2/3=0.6/0.8/1.0`、`path_num=4641`、`path_sample_num=10`、`grid_voxel_num_x/y=90/80` —— **全部吻合**。
- **`basic_server.toml`**：确证速度档位覆盖（FLAT/STAIR/ORIENTEER × LOW/NORMAL/HIGH_SPEED），`stop_distance` 0.6–1.3。
- **`rslidar` `config.yaml`**：`RSAIRY`、`224.10.10.201/.202`、`msop 6691/6692`、`difop 7781/7782`、`imu 6681/6682`、`max_distance=60`、`use_lidar_clock=true`、`send_separately=false`（前后合并）；前外参 `x=0.32028,z=-0.013,pitch=-1.57079,yaw=-3.14159`、后 `x=-0.32028,yaw=0` —— **全部吻合**。
- **`robot_hardware_info.toml`**：`ecan_nic=["eth1"]`、`ecan_uart_port=["/dev/ttyS0"]`、`BOM_version=CA9B_BOM_P1.0_v1.2`、`board_version=PCB-Y25-045_MB_CA9B_V2.0`、`hardware/software_version=3.1.0`、`ecan_version=1.1.1` —— **全部吻合**。

## 5. DDS 图（✅ 属实）

- 可见 **98 个话题**、30+ 服务；`/LIDAR/POINTS`、`/IMU_YESENSE`、`/LIO_ODOM`、`/ODOM`、`/JOINTS_DATA`、`/GRID_MAP`、`/path_Astar`、`/local_goal`、`/planner_mode`、`/NAV_CMD`、`/GLOBAL_PLANNER_STATUS`、`/traversal_cost`、`/vis_global_points_pruned` 全部在列；服务 `/GOAL_GLOBAL`、`/CANCEL_NAV_GLOBAL`、`/CANCEL_NAV_PLANNER`、`/SDK_MODE`、`/encryptionCheck`、`/charge/reflective_column_srv` 全部在列 —— 与 T26 还原**逐项吻合**。
- **未知项定案**：所有业务发布者名为 `_CREATED_BY_BARE_DDS_APP_` —— 原厂用**裸 DDS 参与者**（libdrdds），非标准 ROS 2 节点。这解释了 `ros2 node list` 只见 2 个标准节点（`/accumulate_cloud`、`/passable_area`）。
- QoS：`RELIABLE` + `VOLATILE`。

## 6. 内嵌策略（✅ 属实）

`rl_deploy` 链接 `libonnxruntime.so.1.20.0`，磁盘上**无 `.pt`/`.onnx` 文件**；二进制内引用 `p50_common.pt`/`k1c_common.pt` 等训练侧产物名，策略以明文 ONNX 内嵌。从符号抽取得 **15/15** 有效 ONNX（30 个符号 = 15 × `__name__/__name__len`）。

## 7. ⚠️ 需修正项（3 条）

1. **ECAN ≠ EtherCAT**。`libecanmaster.so` 符号显示 `SocketRaw::Send`、`UdpSocket::updateSingleData(CanFdNetBuffer&, int)`、`CalCRCEPht`、`JointUnit[32]` —— 实为 **CAN-FD 帧承载于以太网（原始套接字 + UDP 双路径）+ CRC**，`eth1` 是标准 `rk_gmac-dwmac`。ECAN 由 `libecanmaster.so` **在 `rl_deploy` 进程内** 处理（**无独立 `ecan-master` 进程**）。dmesg 有内建 `recv/send ecan` 计数（内核内建驱动）。**L1 知识库"EtherCAT 类"表述应更正为"CAN-FD over Ethernet"。**
2. **`rl_deploy` 调度**：`SCHED_RR` 优先级 90（非 `SCHED_FIFO`）。
3. **双雷达冗余定案**：`rslidar`(pid 3806) 持有 `224.10.10.201:6691` 与 `224.10.10.202:6692` 并**真实收包**（5 秒裸捕见 1248B MSOP 持续流入）；`hsLidar`(pid 3821) 持有 `2361/2362` 但**零收包**。**实际生效者为 Robosense `rslidar`**，融合为前后雷达合并（`send_separately=false`）。

## 8. 其他实时观测

- 机间通信：`10.21.33.106 → 10.21.33.103` 的 RTPS 流量（端口 `7412–7452`，524B/包）——**NOS↔AOS 主数据面走 `.33` 网段**（此前仅记 `.31`）。
- FSM：`Basic_server` 日志 `motion state: -1 -> 0`（kIdle）、`gait: 0x0`；`rl_deploy` 日志 `Status Error, Transfer to Joint Damping`（态名吻合）。
- ECAN 固件：`ECAN Program Version: 3.1.6`、`Git Commit V2.0.15_9f08d7e5dc341ede`（与提取的 `.bin` 一致）。
- 当前加载地图：`/var/opt/robot/data/maps/active/occ_grid.yaml`。

---

## 9. 对逆向成果的整体判定

**核心结论全部属实**：三机拓扑、系统栈、8 个关键二进制（含固件）字节一致、四类配置逐项吻合、98 话题/服务清单吻合、15 策略提取无误。
**需修正**：ECAN 协议性质（EtherCAT → CAN-FD over Ethernet）、`rl_deploy` 调度（RR 非 FIFO）。
**已定案未知项**：双雷达实际生效者、DDS 发布者身份（裸 DDS）。
