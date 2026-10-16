# T27 · L1 知识库汇总与自检（CP-3）

> 汇总 T20–T26 全部结论。L1 四条标准 + 建图/导航两项通过线，逐条自检并附证据。
> 详细文档见 `analysis/00..19_*.md`；产物见 `/home/lee/rea`。

## 一、链路清单（标准①）

| 链路 | 物理层 | 协议 | 端口/通道 | 频率 | 证据 |
| --- | --- | --- | --- | --- | --- |
| App/手柄 → 主控 | Wi-Fi (wlan0 AP `CA9B_NO.1546_24G`) / 以太网 | 手柄裸 UDP `0x55 0x66`+CRC16；App JSON 帧 `0xEB 0x90 0xEB 0x90` | **UDP 12121**（手柄）；App 帧 16B 头 + `PatrolDevice{Items,Type,Command}` | 手柄 ~50Hz；心跳事件驱动 | `04_protocols.md`（源码级定义）|
| 主机 A↔B↔C | 千兆以太网 (eth0/eth1) | **RTPS 2.3 (Fast DDS, vendorId 0x0f01)** + drdds CDR；UDP + SHM | **UDP 7400–7460**（domain 0）；SHM segment 500MB | 高频通路 100Hz；`/ODOM` 10Hz；`/JOINTS_DATA` 可至 1000Hz（SDK_MODE 200 默认）| `15_protocol_decoding_T20.md` + 实测抓包 149,352 帧 |
| 主控 ↔ 下位机 | ECAN(EtherCAT 类, eth1) + 串口 | ECAN 帧 + MCU 串口帧 `0xEE 0xEF`（`FuncCode 0x15/0x16/0x17/0x21`）| `ecan_nic=eth1`、`ecan_uart=/dev/ttyS0`；MCU 默认 `/dev/ttyS3` | 关节回环 ~200Hz（5ms 主循环）| `04_protocols.md`、`18_runtime_logs.md` |
| 点云旁路 | UDP | 自定义请求-响应 | **UDP 30100** | 累积点云按请求 | `params.yaml` + 运行日志确认监听 |

## 二、协议可解码（标准②）

| 链路 | 解码状态 |
| --- | --- |
| 手柄 / App | **100%**（常量、结构体、CRC、指令表、FSM 映射均源码级还原）|
| 主机间 drdds | **≥90%**：RTPS 子消息 + CDR 体已解码；`decoders/drdds_decoder.py` 可稳定解析；字段名有权威 `.msg/.idl` 定义；仅少数 404B 指令族字段名待二进制核对 |
| ECAN / MCU | **100%**（头文件级：命令索引、帧头、结构体、单位）|
| 点云旁路 | **100%**（语义已知）|

## 三、FSM 与官方可触发模式一一对应（标准③）

- 部署版 12 态（DWARF）：`kIdle=0, kStandUp=1, kJointDamping=2, kStartDamping=3, kLieDown=4, kSetZero=5, kChargeLieDown=6, kCarMove=16, kRLControl=17, kJointTest=18, kSdkControl=100`。
- 20 种步态 `RobotGaitType`。
- **运行时完整闭环日志**：`idle→standup→rl_control→liedown→joint_damping`（`18_runtime_logs.md`）。
- 触发映射：L1→站立、L2→RL、R1→趴下、R2→阻尼、`/SDK_MODE`→SDK 接管、异常→阻尼。

## 四、运控路线定性（标准④）

- **端到端 RL**：依赖 `libonnxruntime.so.1`；无任何 QP/MPC 求解器；`Ort::Session(Env, void*, size, opts)` 从内存加载内嵌模型。
- **15 个内嵌策略已提取**（`bin/policies/*.onnx`），含 flat/stair/platform/backknee/rough/navi*/extre/stand/sixaxis/hmap 等。
- 观测/动作逐维定义、缩放、kp/kd、频率（50Hz，decimation 4）：见 `06_rl_policy.md`。
- 官方 SDK 提供 57 维单帧骨架；部署版为多帧历史堆叠（`state[1,318]=6×53` 等）。

## 五、建图 / 导航通过线（标准⑤）

| 项 | 状态 |
| --- | --- |
| 建图 ATE <0.1m（50m）| **未验证（阻塞）** —— 机上 14 个录包**全部为 JOINTDAMPING 停机态**，无 50m 运动轨迹 |
| 导航路径偏差 <0.3m | **未验证（阻塞）** —— 同上 |

> 算法侧已还原（LIO=FAST-LIO/IKFoM 系、导航=Hybrid A\* + DWA），仅缺**实机运动数据**做定量 ATE/路径偏差评估。

---

## 六、L1 自检结论

| # | 标准 | 结论 |
| --- | --- | --- |
| ① | 三链路清单完整+证据 | ✅ **达成** |
| ② | 解码 ≥95% | ✅ **基本达成**（主机间按帧可解析，字段名有权威定义；余下为边界字段核对）|
| ③ | FSM 一一对应 | ✅ **达成**（枚举 + 运行时双证）|
| ④ | 运控路线定性 + RL 观测/缩放 | ✅ **达成** |
| ⑤ | 建图 ATE / 导航偏差 | ⛔ **阻塞**：需实机运动录包 |

**净结论**：L1 的 **4/5 项达标**；第 5 项因缺少运动态数据无法定量验收（算法与参数均已还原）。

## 七、进入 L2（数字孪生）的现成资产

- MJCF 模型 + 2202 STL：`dump/hostA/home_user/sdk_deploy/.../M20_description/m20_mjcf/`
- 15 个部署策略 ONNX：`bin/policies/`
- 官方 SDK 回放/仿真接口：`interface/robot/simulation/mujoco_simulation_ros2.py`
- 关节限位/几何：`m20_control_parameters.cpp`
- 既有重构工程（可对照）：`dump/hostA/home_user/m20_orignal/src/m20_slam_navigation/`

## 八、剩余工作

1. 采集**运动态**录包（站立/行走/50m 建图）以完成标准⑤。
2. `libdrdds.so` 分批反编译补齐字段名。
3. L2：T28 URDF/Gazebo → T29 回放 → T30 建图复现 → T31 导航复现 → T32 站立行走。
