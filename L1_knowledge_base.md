# M20 Pro 全栈逆向 — L1 知识库（索引）

> 目标机型：云深处 CA9B（型号 M20，type=PRO），本体编号 CA9B_NO.1546，SN CM20111546。
> 方法：本地有线/无线 SSH 只读勘测 + 官方 SDK 交叉印证 + REA/Ghidra 反编译。
> 机上一律只读；未对运控进程使用 strace/gdb；未写入狗磁盘（ROS daemon HOME 重定向到 tmpfs）。
> 产出根目录：`/home/lee/rea`。

## 0. 结论速览

| 项目 | 结论 |
| --- | --- |
| 机型 | 云深处 CA9B / M20 Pro（轮足混合四足，16 自由度：12 关节 + 4 轮毂） |
| 计算架构 | 3 台 aarch64 主机（8×Cortex-A55, 16GB, 115.3GiB eMMC）：103=AOS 主控/自主，104=GOS，106=NOS 导航 |
| 操作系统 | Ubuntu 20.04.6 LTS aarch64，内核 5.10.198；overlayroot（root 只读 + /userdata 可写） |
| 中间件 | ROS 2 **Foxy** + Fast DDS（rmw_fastrtps），UDP + SHM 传输，自定义消息包 `drdds` |
| 运控路线 | **端到端 RL**（ONNX MLP 57→512→256→128→16），非 MPC/WBC；另有底层关节阻抗 |
| 运动控制 | `rl_deploy`（**SCHED_RR** 90，绑定 CPU4,5）；FSM：idle→standup→rl_control→liedown / joint_damping |
| 状态估计 | LiDAR-惯性里程计（FAST-LIO 系，IKFoM 流形迭代 EKF），双 Robosense Airy |
| 建图 | LIO 建图 + 累积点云（`/var/opt/robot/data/maps/active/full_cloud.pcd`） |
| 导航 | 2.5D 高程图 `height_map_nav` + hybrid A\* 全局规划 + 局部规划（NOS 主机） |
| 总线 | **ECAN = CAN-FD over Ethernet**（`libecanmaster.so` 进程内，原始套接字+UDP 双路径 + CRC，绑 `eth1`；非 EtherCAT），MCU 串口协议（0xEEEF 帧，`/dev/ttyS0/S3`） |
| 上位协议 | 手柄 UDP(0x55 0x66/CRC16, 端口 12121) + App JSON(0xEB90EB90 帧) |
| 官方 SDK | 机上存有 DeepRoboticsLab `sdk_deploy`（M20_sdk_deploy）：FSM/RL 胶水/MJCF/policy.onnx |

## 1. 文档索引

- `01_topology_hosts.md` — 主机与网络拓扑、AOS/GOS/NOS 角色
- `02_software_modules.md` — 进程/服务/模块清单与启动顺序
- `03_middleware_dds.md` — ROS2/DDS 配置、话题与服务全表、UDP 点云接口
- `04_protocols.md` — 四条链路协议：手柄、App JSON、ECAN 电机总线、MCU 串口
- `05_fsm_motion.md` — 运控 FSM、状态定义、安全/泄力路径
- `06_rl_policy.md` — RL 部署侧：观测/动作/归一化/缩放/kp/kd/频率
- `07_slam_mapping.md` — LIO/SLAM 还原（算法、参数、外参、地图）
- `08_navigation.md` — 导航还原（规划器、代价、速度接口）
- `09_hardware.md` — 传感器、总线、MCU、电池、固件资产
- `10_assets.md` — URDF/MJCF/Mesh、ONNX、固件、APK 资产清单
- `11_gaps_and_checklists.md` — 验收自检、未知项、风险与证据缺口
- `12_binary_analysis.md` — 二进制静态分析、FSM 还原、15 个内嵌策略提取
- `13_drdds_messages.md` — drdds 消息/服务完整 schema（协议解码基础）
- `14_task_reports_T21_T23.md` — T21/T22/T23 结论与证据（FSM/RL 路线/策略提取）
- `15_protocol_decoding_T20.md` — 链路/端口 + drdds CDR 解码（真实流量验证）
- `16_runtime_capture_T16_T18.md` — M2 运行时采集报告
- `17_state_est_slam_T24_T25.md` — 状态估计与建图（基于真实录包）
- `18_runtime_logs.md` — 设备自产日志证据（FSM 生命周期/ECAN 版本/授权链）
- `19_navigation_T26_deep.md` — 导航深度还原（Hybrid A\* + DWA 参数级）
- `20_L1_selfcheck_T27.md` — **L1 汇总与自检（CP-3）**
- `23_live_verification.md` — **实机在线只读核验（哈希/配置/DDS 对照 + 3 项修正）**
- `24_obs_layout_extrinsic.md` — **收尾：LiDAR-IMU 外参确证 + 部署观测 53×6 维布局解出**

## 4. 面向二次开发

- **`DEVELOPER_GUIDE.md`** — 架构速查、RL 运控契约（7 种观测变体）、数字孪生使用说明、建图/导航接入、协议对接、二次开发路线与已知边界。
- `21_m4_model_T28.md` — M4 数字孪生模型定义、URDF 与加载验证
- `22_m4_digital_twin.md` — **M4 数字孪生与 L2 验收全量总结 (T28–T32)**
- `sim/locomotion_report.md` — T32 运控闭环站立与行走仿真报告
- `sim/nav_sim_report.md` — T31 闭环导航仿真复现报告
- `sim/mapping_sim_report.md` — T30 真实 281m 建图与轨迹评测报告

## 2. 证据来源（本机留存）

- `dump/hostA/opt_robot/` — 主机 103 `/opt/robot`（274MB，10396 文件，rsync）
- `dump/hostA/home_user/sdk_deploy/` — 官方 SDK 源码（含 policy.onnx、MJCF、APK）
- `dump/hostA/home_user/m20_orignal/` — 机上既有 SLAM/导航重构工程源码
- `runtime/hostA_*.txt` — lsblk/服务/设备/DDS 图 勘测输出
- `sdk/apk_package.json` — REA(JADX) 对 controlapp.apk 的静态分析
- `env_report.json` — REA doctor 就绪报告
- `bin/`、`analysis/` — 二进制定位与反编译产物（见各模块文档）

## 3. 与计划文档的偏差（已记录）

1. **主机数量**：计划假设 2 台主机；实测 **3 台**（103/104/106），另有 105(vos) 角色未上机。
2. **ROS 版本**：计划假设 Humble；实测 **Foxy**（Ubuntu 20.04 匹配）。
3. **凭据**：计划假设 root SSH；实测登录用户 `user`（uid 1003，sudo 需密码，密码为单引号 `'`）。
4. **REA 宿主**：计划假设 `rea doctor` 健康；实测宿主为 Ubuntu 22.04（REA 官方不支持），但 **Ghidra provider 实测 healthy**，故未启用 Docker 回退（R5）。另：APK 分析需额外提供 `jadx-headless-mcp 0.7.1`（已按官方校验值安装）。
5. **LLM 侧分析引擎**：计划写 Ghidra 11.x；REA 现要求 **Ghidra 12.1.x**（已安装 12.1.4）。
6. **全盘镜像**：因目标 Wi-Fi 信号弱（-74dBm，实测 ≈1.2MB/s），改为**分块可续传镜像**（512MiB/块，独立 gzip 成员可拼接），后台执行；镜像落盘至 `/media/lee/数据/rea_images/`（本机 `/` 仅余 ~53GB）。
7. **点云第二个驱动**：实测同时存在 `rslidar`(Robosense SDK) 与 `hsLidar`(Hesai SDK) 两个驱动二进制监听同一对雷达，需运行时确认实际生效者。

---
_最后更新：M1–M4 全阶段完成（L1 知识库 + L2 数字孪生均已交付）。_
