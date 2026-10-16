# 11 · 验收自检、未知项与风险

## 1. 计划任务执行状态（M0/M1 阶段）

| 任务 | 状态 | 产物 / 证据 |
| --- | --- | --- |
| T01 本地工具链 + REA 就绪 | ✅ 完成 | node v24.14.1；REA 6.4.0；`rea setup --client opencode` 已注册 MCP（本会话已见 `rea` 工具集）；`env_report.json`。**宿主为 Ubuntu 22.04（REA 标不支持），但 Ghidra provider healthy，未触发 Docker 回退** |
| T02 Ghidra + JDK | ✅ 完成 | Ghidra 12.1.4 @ `/opt/ghidra_12.1.4_PUBLIC`；JDK 21；`rea doctor --provider ghidra` → ghidra/native_decompiler healthy |
| T03 两机存储勘测 | ✅ 完成（实为三机） | `runtime/hostA_lsblk.txt`；104/106 经 `rsudo.sh` 实测；命名 `hostA_103/hostB_104/hostC_106` |
| T04 主机A 全盘镜像 | ⏳ 进行中（后台分块） | `images/imaging.log`；`/media/lee/数据/rea_images/hostA_103/` |
| T05 主机B 全盘镜像 | ⏳ 排队 | 镜像脚本按 103→104→106 顺序 |
| T06 核心目录 rsync | ✅ 完成 | `dump/hostA/opt_robot`（274MB/10396 文件，仅 4 个 root lock 文件失败）；`dump/hostA/home_user/*` |
| T07 凭据隔离 | ⏳ 待做 | 已定位 `scripts/board_resources/wifi/password`、`home_user/.ssh`、`.gnupg` 等；待归入 `QUARANTINE/` |
| T08 资产搜刮 | ✅ 主要完成 | MJCF+2202 STL、policy.onnx、15 个部署策略、固件、APK —— 见 10 节 |
| T09 OTA/固件搜寻 | ✅ 主要完成 | `CA9B_f1_app_v2.1.0.bin`、`ecan_V2.0.15_*.bin`、`firmware_upgrade.sh`、`FirmwareAssistant/DriverOTA/BatteryOTA` |
| T10 进程/服务拓扑 | ✅ 完成 | AOS/GOS/NOS 三机服务与进程（02 节 + `runtime/hostA_services.txt`） |
| T11 外设/总线勘测 | ✅ 完成 | 串口/I2C/USB/eth；**无 CAN**、EtherCAT(eth1) + 串口（09/04 节） |
| T12 IPC/中间件识别 | ✅ 完成 | ROS2 Foxy + Fast DDS（UDP+SHM），`runtime/hostA_dds.txt`（170 行话题/服务） |
| T13 SDK/APK 静态分析 | ✅ 完成 | 官方 SDK 源码 + `sdk/controlapp.apk`（REA/JADX）+ 手柄/App 协议（04 节） |
| T14 主控二进制定位 | ✅ 完成 | 3 类主二进制定位；**未剥离**居多；REA+Ghidra 已入库 basic_server（12 节） |
| T15 CP-1 吊架安全基准 | ⛔ 人工检查点 | 清单已备：`runtime/safety_checklist_CP1.md`；**待用户确认** |
| T21 FSM 与模式切换 | ✅ 完成（提前） | 14 节：DWARF 枚举级证据，12 态 + 20 步态 |
| T22 运控路线判定 | ✅ 完成（提前） | 14 节：判定 RL；依赖 `libonnxruntime`，无 QP/MPC 库 |
| T23 RL 部署侧还原 | ✅ 完成（提前） | 14 节：15 个策略提取 + 观测/动作缩放/kp/kd |

## 2. L1 验收标准自检（CP-3）

| 标准 | 现状 | 证据/缺口 |
| --- | --- | --- |
| ① 三条链路清单完整（物理层/协议/端口/频率 + 证据） | **达成** | 04/15/16 节：手柄 UDP12121、App EB90EB90 JSON、主机间 FastDDS(7400–7460)、ECAN(eth1)、MCU 串口(0xEEEF)；含实测抓包 |
| ② 各链路解码 ≥95% 帧可解析 | 基本达成 | 15 节：RTPS+CDR 解码器已验证（`/ODOM` 布局锁定、312B 高频帧可稳定解析）；待补 drdds 字段名（反编译 `libdrdds.so`）|
| ③ FSM 与官方可触发模式一一对应 | **达成** | 05/14/18 节：DWARF 枚举 + **运行时完整生命周期日志**双重确证 |
| ④ 运控路线定性 + RL 观测每维/动作缩放 | **达成** | 06/12/14 节：判定端到端 RL；依赖 `libonnxruntime`、无 QP/MPC；15 个内嵌策略已提取 |
| ⑤ 建图 ATE <0.1m；导航路径偏差 <0.3m | 未验证 | **阻塞**：机上 14 个录包**全部为 JOINTDAMPING（停机）状态**，无 50m 运动数据；需现场跑图或用户提供运动态录包 |

## 3. 关键未知项

1. ~~**部署观测与 SDK 观测不一致**：部署策略输入 318 维（疑 6 帧 × 53），SDK 为 57 维单帧。~~ → **已确证（T33）**：`obs_dim_=53`、`obs_history_num_=5`、`obs_total_dim_=318`；每帧 = `ω·0.25(3) + 重力(3) + cmd(3) + (dof_pos−default)(12，关节主序) + dof_vel·0.05(12) + wheel_vel·scale(4) + last_action(16)`。见 `24_obs_layout_extrinsic.md`。
2. **DDS 发现范围**：`ros2 node list` 仅见 4 节点，与运行进程数不符 → 业务节点可能用非标准 participant/netns，跨机发现与 topic↔node 映射待定。
3. ~~**双雷达驱动冗余**：`rslidar` 与 `hsLidar` 同时运行，实际生效者待确认。~~ → **已确证（实机只读核验）**：`rslidar`(pid 3806) 持有 `224.10.10.201:6691`/`.202:6692` 且**真实收包**；`hsLidar`(pid 3821) 持有 `2361/2362` 但**零收包**。实际生效者为 **Robosense `rslidar`**（`send_separately=false` 前后合并）。
4. **LiDAR-IMU 外参**：配置为单位阵，真实外参可能在二进制内。
5. **`.pt` 与 `.onnx`**：二进制含 `../policy/p50_common.pt` 字符串且内嵌 ONNX；加载优先级/是否运行时由 `.pt` 转换待确认。
6. **ROS_DOMAIN_ID**：未显式设置（疑默认 0），与 SDK 文档 `ROS_DOMAIN_ID=1` 不同。
7. **摄像头未枚举**（`/dev/video*` 为空）。
8. **MCU 读保护**：`CA9B_f1_app_v2.1.0.bin` 为 OTA 包（可静态分析）；是否可从 SWD 读回需 L3。

## 4. 风险回退（对照计划 R1–R7）

- **R1（模型加密/硬件绑定）**：**已解除** —— 权重以明文 ONNX 内嵌于二进制，已提取 15 个。
- **R2（去符号/OLLVM）**：**大幅降低** —— 主控二进制未剥离、未混淆。
- **R3（MCU RDP）**：不影响 L1/L2 —— OTA 固件已入手，可静态分析；直读属 L3。
- **R4（录制伤人）**：无录制动作发生（未进 M2）。
- **R5（REA 与 22.04 不兼容）**：Ghidra provider 实测 healthy，未回退 Docker；若后续 provider 异常再启用 24.04 容器。
- **R6（dd 写反/变砖）**：镜像全部 `if=狗盘 of=本地`；已用 `gzip -t` 校验每块。
- **R7（云端外发）**：仅技术性隔离未完成（T07 待做）。

## 5. 下一步（进入 M2 前的门）

- 完成 T04/T05 镜像（后台）。
- 完成 T07 凭据隔离。
- 用 REA/Ghidra 反编译 `lio_ddsnode`、`ecan-master`（剥离）补齐 T22/T25。
- 归整机上 `rob_bag` 录包作为 T19 替代数据（可省去部分现场采集）。
- **CP-1 人工检查点：任意运行时录制前必须由用户确认吊架/急停/场地。**
