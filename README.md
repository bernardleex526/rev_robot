# rev_robot — DeepRobotics M20 Pro 全栈逆向

本仓库是对云深处（DeepRobotics）**M20 Pro / CA9B**（16 自由度轮足机器狗）的独立逆向与互操作研究。材料来自实机只读勘测、官方 SDK 交叉印证，以及 REA/Ghidra 反编译。

> **性质声明**：本仓库不是云深处官方源码，也不代表与原厂二进制 1:1 等价。所有结论仅供研究、互操作和安全评估使用；实机运动、固件刷写和底层总线操作有风险，必须由授权人员在硬急停可用、有人监护的环境中执行。

## 先读什么

| 文档 | 内容 |
| --- | --- |
| [`L1_knowledge_base.md`](L1_knowledge_base.md) | L1 总索引：三主机、DDS、FSM、RL、SLAM、导航、硬件 |
| [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) | 二次开发主文档：目录地图、RL 契约、数字孪生、部署边界 |
| [`M20_WSL二次开发技术文档.md`](M20_WSL二次开发技术文档.md) | 独立复核结论、已确认的错误/过时结论与修正建议 |
| [`M20_WSL仿真部署指南.md`](M20_WSL仿真部署指南.md) | WSL2 + Gazebo Classic 11 + MuJoCo 的仿真部署 |
| [`STATUS.md`](STATUS.md) | M0–M4 里程碑与实机核验状态 |

## 仓库结构与产物边界

| 路径 | 内容 | 性质 |
| --- | --- | --- |
| `analysis/` | 24 篇专题报告：拓扑、协议、FSM、RL、SLAM、导航、硬件、二进制 | **直接逆向分析产物** |
| `L1_knowledge_base.md`、`DEVELOPER_GUIDE.md`、`STATUS.md` | 知识库、开发指南、状态报告 | **直接逆向总结** |
| `notes/` | Ghidra 反编译原始输出：外参、观测布局、策略映射、runner 参数 | **直接逆向证据** |
| `tools/` | Ghidra/pyelftools 脚本、ONNX 提取脚本、runner 参数解析 | **直接逆向工具** |
| `decoders/` | RTPS/CDR、drdds 消息、rosbag 里程计解码器 | **直接逆向工具** |
| `sim/` | 数字孪生、策略回放、导航闭环、建图评测 | **直接逆向复现产物**；其中 `sim/m20_description/` 来自官方 MJCF/STL，`sim/ws/src/m20_slam_navigation/` 是行为级重建副本 |
| `m20_sim/` | WSL 下的 Gazebo/MuJoCo 仿真源码、SDK 补丁、测试脚本 | 验证/移植产物；基于官方 SDK、MJCF 和实机 dump |
| `m20_wsl_scripts/` | WSL 环境、drdds 重建、官方 SDK 构建、sim-to-sim 冒烟测试 | 验证/移植脚本 |
| `bin/` | 实机二进制、符号/布局、`bin/policies/*.onnx`（15 个从 `rl_deploy` 提取的部署策略） | **原始素材 + 静态分析/提取产物** |
| `dump/` | AOS `/opt/robot`、官方 SDK、机上既有 SLAM/导航工程、NOS 工具链 | **实机只读原始素材**，非逆向分析产物 |
| `captures/` | pcap 抓包、ROS 2 bag、200 Hz 关节/IMU/状态 CSV | **运行时原始素材** |
| `sdk/` | `controlapp.apk` 与 JADX 元数据 | **原始 APK + 静态分析产物** |
| `images/`、`runtime/`、`assets/` | 全盘镜像进度、勘测输出、资产清单 | **原始素材/清单** |

> 简单判断：**`analysis/`、`notes/`、`tools/`、`decoders/`、`sim/` 和本 README 属于逆向产物；`dump/`、`captures/`、`bin/`、`sdk/` 是逆向的输入素材；`m20_sim/`、`m20_wsl_scripts/` 是验证/移植产物。**

## 快速开始

### 环境

- Ubuntu 22.04 / ROS 2 Humble（Windows 下建议 WSL2）
- Gazebo Classic 11（仅 `m20_sim/` 的 Gazebo 链路需要）
- Python 3.10、MuJoCo、ONNX Runtime
- 无需先安装厂商 `libdrdds.so`：`drdds` 消息包由 `dump/` 中的 `.msg/.srv` 在 Humble 下重建

### 1. 构建 drdds + 官方 SDK（x86）

```bash
cd rev_robot
bash m20_wsl_scripts/00_setup_python_venv.sh
REPO="$PWD" W=~/m20_ws bash m20_wsl_scripts/01_build_drdds_and_sdk.sh
W=~/m20_ws bash m20_wsl_scripts/02_sdk_sim2sim_headless.sh
```

`01_build_drdds_and_sdk.sh` 会使用 `dump/hostA/ros_foxy_share/{msg,srv}` 和官方 `M20_sdk_deploy`。如果 Git LFS 文件未拉取，先执行：

```bash
git lfs pull
```

### 2. 部署策略数字孪生（MuJoCo）

```bash
~/.venvs/m20/bin/python sim/validate_model.py
~/.venvs/m20/bin/python sim/replay_eval.py
~/.venvs/m20/bin/python sim/sim2sim_deployed.py \
  bin/policies/policy_policy_m20_50.onnx 10 0.5 M20BasicFlatRunner
```

参数格式：`<onnx> <秒> <vx> <Runner> [gait_freq]`。脚本按 `Path(__file__)` 定位，不依赖 `/home/lee/rea`。

### 3. Gazebo / MuJoCo 仿真环境

```bash
REPO="$PWD" W=~/m20_sim_ws bash m20_sim/setup_m20_sim.sh
source ~/m20_sim_ws/env.sh
ros2 launch m20_gazebo m20_gazebo.launch.py rl_deploy:=true
```

无界面运行：

```bash
ros2 launch m20_gazebo m20_gazebo.launch.py gui:=false rl_deploy:=true
```

详细说明、MuJoCo 进程内运行方式和已知问题见 [`M20_WSL仿真部署指南.md`](M20_WSL仿真部署指南.md)。

## 已验证结果

- **二进制一致性**：`rl_deploy`、`basic_server`、`lio_ddsnode`、`astar_node`、`localPlanner`、`localization_ddsnode`、`handler`、ECAN 固件共 8 个关键二进制/固件与实机哈希逐一一致（`analysis/23_live_verification.md`）。
- **策略提取**：从 `rl_deploy` 中提取 15 个明文 ONNX 策略；`replay_eval.py` 可执行性 15/15，双向关节标定误差约 `4.4e-16 rad`。
- **数字孪生闭环**：15 个部署策略中 14 个完成站立/行走闭环；`NaviCharge` 是确定的失败项（`sim/deployed_regression.md`）。
- **状态估计**：LiDAR-IMU 外参确证为 identity；部署观测布局为 `obs_dim=53`、`history=5`、`obs_total_dim=318`（`analysis/24_obs_layout_extrinsic.md`）。
- **导航复现**：Hybrid A* + DWA/LinePlanner 在自写运动学仿真中完成直线、斜向、绕障三场景，零碰撞（`sim/nav_sim_report.md`）；这是离线复现，不是实机验收。

## 已知边界与修正

1. **`sim2sim_deployed.py` 的 `WHEEL_VEL_SCALE`**：全局默认 `0.05` 与基类反编译值 `0.01` 不一致，影响部分 runner；修正与影响见 [`M20_WSL二次开发技术文档.md`](M20_WSL二次开发技术文档.md) §2.1。
2. **281 m 走航数据**：早期文档中的“281.85 m、平均 6.46 m/s”基本可判定为 `/ODOM` 漂移/坐标或单位问题，**不要作为 SLAM 精度基准**；详见复核文档 §2.1。
3. **`NaviCharge`**：观测与软启动已还原，但零指令下会持续移动，不能当作普通站立策略使用。
4. **`cal_command`**：多输入族的完整语义尚未逆向，目前只确认 `command[0]=v_x` 有效。
5. **训练端**：奖励函数、域随机化、课程学习未逆向，需自行设计。
6. **L3 硬件替换**：底层电机/ECAN 逐字节协议、SWD/吊架实验未完成，仓库不提供可直接上实机的底层控制。
7. **`lio_ddsnode`**：已剥离符号，与开源 FAST-LIO 的差异属于行为级验证，不是源码级等价证明。

## 安全与分发

- **厂商资产**：`dump/`、`bin/`、`bin/policies/*.onnx`、`sdk/controlapp.apk`、MJCF/STL 等版权归云深处或各自权利人所有。本仓库用于研究与互操作，**不应再分发这些原始资产**；对外发布前请自行确认授权。
- **凭据**：仓库根目录的 `dogssh.sh`、`dogsudo.sh`、`rsudo.sh`、`env.sh` 含明文 SSH/sudo 密码。使用前请轮换密码、改为环境变量，并用 `git filter-repo` 清理历史。`QUARANTINE/` 已被 `.gitignore` 排除。
- **实机安全**：仓库中的速度、步态、关节指令和 UDP/TCP 协议示例均不是安全认证配置。任何实机运动都必须先完成标定、包络检查、硬急停和人工监护；不要仅凭仿真结果下发运动指令。

## 许可证

本仓库未附开源许可证。原始分析文档和脚本可按研究目的参考；厂商二进制、ONNX 权重、APK、MJCF/STL 等不因本仓库而改变其原有授权。引用本项目时请注明仓库地址。
