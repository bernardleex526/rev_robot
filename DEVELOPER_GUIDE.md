# 云深处 M20 Pro 逆向成果 — 二次开发指南

> 版本：v1.0 　 适用机型：云深处 CA9B / M20 Pro（轮足混合四足，16 自由度）
> 产物根目录：`/home/lee/rea` 　 全部结论均有实机只读验证或二进制证据支撑
> 本文件面向**二次开发**：拿现有成果做新控制器、新导航、新上位机、或新仿真实验

---

## 0. 快速导航

| 我想做… | 直接看 | 关键文件 |
| --- | --- | --- |
| 跑起来看看数字孪生 | §5 | `sim/sim2sim_deployed.py` |
| 写自己的运控策略 | §4 + §5.4 | `sim/runner_params.json`、`bin/policies/*.onnx` |
| 对接实机下发电机指令 | §3 + §6 | `analysis/04_protocols.md`、`analysis/13_drdds_messages.md` |
| 做导航/建图二次开发 | §7 | `dump/hostC_opt_robot/`、`analysis/19_navigation_T26_deep.md` |
| 了解系统全貌 | §2 | `L1_knowledge_base.md` |
| 接入真实传感器数据 | §6 | `decoders/` |

---

## 1. 成果总览

### 1.1 交付层级

| 层级 | 内容 | 状态 |
| --- | --- | --- |
| **L1 知识库** | 系统架构、四类通信链路、FSM、RL 运控、SLAM、导航的完整还原 | ✅ 完成 |
| **L2 数字孪生** | MuJoCo 模型 + 真实部署权重闭环（14/15 策略站走通过）| ✅ 完成 |
| **L3 硬件替换** | 自研底层控制下发电机指令 | ⏸ 推迟（需拆机/吊架）|
| **训练端重建** | 奖励函数 / 域随机化 / 课程学习 | ⏸ 推迟（需算力）|

### 1.2 目录地图

```
rev_robot/（原产出根目录 /home/lee/rea/）
├── README.md                     # 仓库入口、边界与快速开始
├── L1_knowledge_base.md          # L1 总索引（从这里开始）
├── DEVELOPER_GUIDE.md            # ★ 本文件：面向二次开发的完整文档
├── STATUS.md                     # 当前任务状态
├── M20_WSL二次开发技术文档.md    # 独立复核结论与已知修正
├── M20_WSL仿真部署指南.md        # Gazebo / MuJoCo 仿真部署
│
├── analysis/                     # 24 篇技术文档（按主题编号）
│   ├── 01_topology_hosts.md      #   三主机与网络拓扑
│   ├── 02_software_modules.md    #   进程/服务/启动顺序
│   ├── 03_middleware_dds.md      #   ROS2/DDS、话题服务全表
│   ├── 04_protocols.md           #   四条链路协议（手柄/App/ECAN/MCU）
│   ├── 05_fsm_motion.md          #   运控 FSM（12 态 + 20 步态）
│   ├── 06_rl_policy.md           #   RL 部署侧观测/动作/缩放
│   ├── 07_slam_mapping.md        #   LIO/SLAM 还原
│   ├── 08_navigation.md          #   导航还原
│   ├── 09_hardware.md            #   传感器/总线/MCU/电池/固件
│   ├── 10_assets.md              #   URDF/MJCF/Mesh/ONNX/固件/APK 清单
│   ├── 11_gaps_and_checklists.md #   验收自检、未知项
│   ├── 12_binary_analysis.md     #   二进制静态分析
│   ├── 13_drdds_messages.md      #   drdds 消息/服务完整 schema
│   ├── 14..20_*.md               #   各任务专题报告
│   ├── 21_m4_model_T28.md        #   M4 模型定义
│   ├── 22_m4_digital_twin.md     #   M4 全量总结
│   ├── 23_live_verification.md   #   实机在线只读核验（哈希对照）
│   └── 24_obs_layout_extrinsic.md#   ★ 外参 + 观测布局权威解出
│
├── bin/                          # 二进制与提取物
│   ├── rl_deploy                 #   运控主程序（未剥离，含 DWARF）
│   ├── basic_server              #   安全仲裁/接口服务
│   ├── lio_ddsnode               #   LIO 里程计（已剥离）
│   ├── *_symbols.txt / *_needed.txt  # 符号、关键字符串
│   ├── rl_deploy_enums.txt       #   FSM 枚举（DWARF 提取）
│   └── policies/*.onnx           #   ★ 15 个部署策略（明文权重）
│
├── sim/                          # ★ 数字孪生（二次开发主战场）
│   ├── sim2sim_deployed.py       #   ★ 用真实部署权重跑 MuJoCo（核心脚本）
│   ├── sim2sim_stand_sdk.py      #   用 SDK 57 维策略跑 MuJoCo（备选）
│   ├── runner_params.json        #   ★ 14 个 runner 的参数表
│   ├── m20_description/          #   MJCF + 2202 STL + URDF + calibration.json
│   ├── nav_sim/nav_closed_loop   #   导航闭环评测（Hybrid A* + DWA）
│   ├── ws/                       #   ROS 2 工作区（m20_slam_navigation）
│   ├── validate_model.py         #   模型结构校验
│   ├── replay_eval.py            #   策略可执行性 + 标定校验
│   ├── mapping_eval.py           #   281m 真实数据建图评测
│   ├── deployed_regression.md    #   ★ 策略回归报告（7 变体表）
│   ├── locomotion_report.md      #   T32 站立行走报告
│   ├── nav_sim_report.md         #   T31 导航报告
│   └── mapping_sim_report.md     #   T30 建图报告
│
├── m20_sim/                      # WSL Gazebo/MuJoCo 仿真源码（基于官方 SDK/MJCF）
├── m20_wsl_scripts/              # WSL 环境、drdds 重建与 SDK 构建脚本
│
├── dump/                         # 从实机拉取的原始文件（只读证据）
│   ├── hostA/opt_robot/          #   AOS /opt/robot（274MB）
│   ├── hostA/home_user/sdk_deploy/   # 官方 SDK 源码
│   ├── hostA/home_user/m20_orignal/  # 机上既有 SLAM/导航工程
│   └── hostC_opt_robot/          #   NOS 导航工具链（103 文件）
│
├── captures/                     # 运行时抓包与数据
│   ├── app_interhost.pcap        #   上层链路抓包
│   ├── interhost_full.pcap       #   机间抓包
│   ├── bag/                      #   ROS 2 bag（含 281m 真实走航数据）
│   └── csv/                      #   200Hz 关节/IMU/状态 CSV 快照
│
├── decoders/                     # 协议解码器（Python）
├── tools/                        # 逆向工具（Ghidra/pyelftools 脚本）
├── notes/                        # 反编译原始输出（证据留档）
├── QUARANTINE/                   # 敏感凭据（已隔离，勿分发）
└── venv/                         # Python 环境（mujoco/onnxruntime/pyelftools）
```

---

## 2. 系统架构（二次开发速查）

### 2.1 三主机

| 主机 | IP | 角色 | 关键进程 |
| --- | --- | --- | --- |
| **AOS** | `10.21.31.103`（`wlan0=10.21.41.1`）| 主控/自主 | `rl_deploy`、`basic_server`、`lio_ddsnode`、`height_map_nav`、`rslidar`、`ctrlmcu_node` |
| **GOS** | `10.21.31.104` | 外部接入 | 4G/5G、Wi-Fi、视频推流、OTA |
| **NOS** | `10.21.31.106` | 导航 | `astar_node`、`localPlanner`、`pcl_pass_grid`、`localization_ddsnode`、`handler` |

- OS：Ubuntu 20.04.6 aarch64，内核 5.10.198
- 中间件：**ROS 2 Foxy + Fast DDS 2.14**；业务节点用**裸 DDS 参与者**（`_CREATED_BY_BARE_DDS_APP_`），故 `ros2 node list` 看不到它们（`ros2 topic list` 正常）

### 2.2 四条通信链路

| 链路 | 物理 | 协议 | 文档 |
| --- | --- | --- | --- |
| 手柄 → 主控 | Wi-Fi | 裸 UDP，`0x55 0x66` 头 + CRC16，端口 **12121** | `04_protocols.md` §① |
| App → 主控 | Wi-Fi/云 | 帧头 `0xEB 0x90 0xEB 0x90` + JSON | `04_protocols.md` §② |
| 主控 ↔ 电机 | `eth1` | **ECAN = CAN-FD over Ethernet**（原始套接字+UDP，CRC），`libecanmaster.so` 在 `rl_deploy` 进程内 | `04_protocols.md` §③ |
| 主控 ↔ MCU | 串口 `/dev/ttyS0,S3` | `0xEE 0xEF` 帧头 | `04_protocols.md` §④ |
| 机间 | 板载以太网 `.31`/`.33` | Fast DDS RTPS（UDP 7400–7460） | `03_middleware_dds.md` |

> ⚠️ 常见误解更正：ECAN **不是 EtherCAT**；`rl_deploy` 调度是 **SCHED_RR** 优先 90（非 FIFO）。

### 2.3 运控数据流

```
双 Robosense Airy LiDAR ──UDP 6691/6692──► rslidar 驱动 ─┐
                    （前后雷达合并、外参 x=±0.32028）    │
Yesense IMU ──/dev/ttyS9──► yesense_node ────────────────┤
                                                          ▼
                          /LIDAR/POINTS(10Hz) + /IMU_YESENSE(200Hz)
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
        lio_ddsnode (FAST-LIO/IEKF)          NOS: astar_node + localPlanner
          └─► /LIO_ODOM /ODOM                 └─► /NAV_CMD
                                     │
                                     ▼
                    rl_deploy: FSM → RL 策略 → ECAN → 电机
```

---

## 3. FSM 与运控（二次开发必读）

### 3.1 状态机（DWARF 权威提取 + 运行时日志双证）

```
kIdle=0 → kStandUp=1 → kRLControl=17 ──► kLieDown=4 → kJointDamping=2
                     ╲                  ╱
                      kStartDamping=3, kSetZero=5, kChargeLieDown=6,
                      kCarMove=16, kJointTest=18, kSdkControl=100
```

- 20 种步态（`GAIT` 枚举，如 `4097` = BasicFlat、`0x1004` = …）
- 进入 RL 前必须经 `kStandUp`（缓启动到站立位姿），**不能直接从趴姿进 RL**

### 3.2 关节域约定（关键！）

```
机身/发布域角 = MJCF qpos 角（同一约定）
前腿：hipy<0（大腿朝下）、knee>0
后腿：hipy>0、knee<0（镜像）
```

- `lio_ddsnode` 的 `params.yaml` 中 `extrinsic_B_I` / `extrinsic_B_L` 均为**单位阵**——LIO 视点云帧与 IMU 帧重合；真实雷达安装由 **rslidar 驱动**承担（前后合并输出到机身中心帧，实测点云 `r<0.3m` 无点）
- 示例脚本里的 `JOINT_DIR` / `POS_OFFSET_DEG` 是**实机编码器域 → 发布域**的转换，**对 MJCF 不适用**（MJCF 已在发布域）

---

## 4. ★ RL 运控契约（二次开发核心）

> 来源：`bin/rl_deploy`（含 DWARF）反编译，脚本 `tools/ghidra_rl_obs.py` / `ghidra_policy_map.py` / `parse_runner_params.py`
> 完整报告：`analysis/24_obs_layout_extrinsic.md`、`sim/deployed_regression.md`

### 4.1 策略↔runner 权威映射

策略以**链接期符号** `__policy_<name>_` 内嵌于二进制（明文 ONNX），由各 runner 构造函数引用：

| 策略名 | runner 类 | obs 规格 |
| --- | --- | --- |
| `policy_policy_m20_38` / `_50` | `M20BasicFlatRunner` | A / 53 |
| `policy_policy_m20_5` | `M20BasicStairRunner` / `M20NaviStairRunner` | A / 53 |
| `policy_policy_m20_backknee6` | `M20BasicBackkneeRunner` | A / 53 |
| `policy_policy_m20_rough_6` | （未检出 xref；实测 `BasicStair` 可用）| A / 53 |
| `policy_policy_ca9bplatform` | `M20BasicPlatRunner` | **B** / 53 |
| `policy_m20_navi_stair_v7_0_himloco` | `M20NaviOrienteerRunner` | A / 53 |
| `policy_m20_navi_flat_v4_2` | `M20NaviFlatPolicyRunner` | **D** / 54 |
| `policy_m20_navi_charge_v3_29` | `M20NaviChargePolicyRunner` | **C** / 60 |
| `policy_m20_flat_v1_4` | `M20StandPolicyRunner` | **E** / 61 |
| `policy_m20_forward_policy_2` | `M20ExtrePolicyRunner` | **F** / 53×36 |
| `policy_m20_finetune_stand_15kg` | `M20FinetuneStandRunner` | **F** / 53×36 |
| `policy_m20_sixaxis_stand` | `M20SixAxisStandRunner` | **F** / 53×36 |
| `policy_m20_finetune_forward` | `M20StepMoveRunner` | **F** / 53×36 |
| `policy_m20_hmap_motion_v0_2` | `M20HeightGapPolicyRunner` | **G** / 504×6 |

### 4.2 七种观测变体

**基础项（所有变体共用）**：
```
ω_body × 0.25            (3)    # 机体系角速度 × omega_scale_
Rᵀ · [0,0,-1]            (3)    # 投影重力
cmd_vel × [1,1,0.25]     (3)    # 速度指令 × cmd_vel_scale_
dof_pos − dof_default    (12)   # 见 §4.3 关节序
dof_vel × 0.05           (12)
wheel_vel × wheel_scale  (4)
last_action              (16)   # 上一帧动作
```
基础合计 **53**。

| 变体 | 追加内容 | 维度 | 使用者 |
| --- | --- | --- | --- |
| **A** | — | 53 | 多数 runner |
| **B** | 关节项改**腿主序**、动作**机器人序直用** | 53 | `BasicPlatRunner` |
| **D** | cmd 之后插常量 `0.52` | 54 | `NaviFlatPolicyRunner` |
| **C** | cmd 之后插 `sin(2π·φ)`、`cos(2π·φ)`、`gait_commands(5)` | 60 | `NaviChargePolicyRunner` |
| **E** | B + 步态 3 项 + 末尾常量 `1.0` | 61 | `StandPolicyRunner` |
| **F** | 多输入：`state[1,36,53]` + `command[1,N]` + `uncertain[1,1]≡1.0` | 53×36 | `Extre`/`FinetuneStand`/`SixAxisStand`/`StepMove` |
| **G** | A + 高程图 `hmap_data×5.0`（41×11=451，末尾）| 504×6 | `HeightGapPolicyRunner` |

**历史帧**：A–E/G 为 `[当前帧 | 历史窗口(5帧)]`（`obs_history_num_=5`，左移+追尾）；F 为整段 36 帧 `state[1,36,53]`。

**步态相位**：`φ += gait_commands[0] × 0.02`（策略 50Hz），取模 1.0。

### 4.3 关节排序（两种序，务必分清）

```
机器人序 robot order： [FL(hipx,hipy,knee,wheel), FR(...), HL(...), HR(...)]   16 维
关节主序 joint-major： [hipx×4, hipy×4, knee×4]  (FL,FR,HL,HR)                 12 维
腿主序   leg-major  ： [FL3, FR3, HL3, HR3]                                    12 维
```
- 变体 A/C/D/E(观测)/F 的 `dof_pos` = **关节主序** 或 **腿主序**（见变体表）
- 动作输出：变体 A/C/D/G 为**关节主序**；B/E/F 为**机器人序**

### 4.4 动作 → 关节目标

```
# 变体 A/C/D/G（关节主序动作，经 4×4 转置）
goal_pos[leg*4 + j] = act[j*4 + leg] * action_scale + dof_pos_default_[leg*3 + j]   (j=0..2)
goal_vel[leg*4 + 3] = wheel_action_scale * act[12 + leg]

# 变体 B/E/F（机器人序动作，直用）
goal_pos[leg*4 + j] = act[leg*4 + j] * action_scale + dof_pos_default_[leg*3 + j]
goal_vel[leg*4 + 3] = wheel_action_scale * act[leg*4 + 3]

# 输出先钳位：act = clip(act, -100, 100)
# 力矩：tau = kp*(goal_pos − pos) + kd*(goal_vel − vel)
```

### 4.5 逐 runner 真值（`sim/runner_params.json`）

| runner | kp | kd | dof_pos_default（腿主序）| gait_commands |
| --- | --- | --- | --- | --- |
| `BasicFlat`/`BasicStair`/`NaviStair` | `[80,80,80,0]×4` | `[3,3,3,0.6]×4` | `(-0.1,-0.8,1.6)`/`(-0.1,0.8,-1.6)` | — |
| `BasicBackknee` | `[80,80,80,0]×4` | `[3,3,3,0.6]×4` | 四腿膝均 `+1.6` | — |
| `BasicPlat` | `[80,80,80,0]×4` | `[3,3,3,0.6]×4` | `(±0.1,-0.6,1.05)` | — |
| `Navi*`（charge/flat/orienteer/heightgap）| 见下 | 见下 | hipx 全 `0.0`，`(-0.8,1.6)`/`(0.8,-1.6)` | — |
| `NaviCharge` | `[60,60,60,0]×4` | `[1.5,1.5,1.5,0.6]×4` | 同上 | `[1.5,0.5,0,0,0.5]` |
| `StandPolicy` | `[80,100,100,0]×4` | `[2,2,2,0.6]×4` | `(±0.1,-0.75,1.5)`/`(±0.1,0.75,-1.5)` | `[2.0,0.5,0,0,0.5]` |

**全局常量**：`action_scale_=0.25`、`wheel_action_scale_=10.0`、`omega_scale_=0.25`、`dof_vel_scale_=0.05`、`wheel_vel_scale_=0.01`（部分 runner 覆写为 0.05）、`cmd_vel_scale_=[1,1,0.25]`、`decimation_=20`（策略 50Hz）。

### 4.6 软启动（`NaviCharge` 特有，重要）

```cpp
if (run_cnt_ <= obs_history_num_ * 2) {   // 前 10 个策略步
    kp_eff = kp_ * 0.5;
    kd_eff = kd_ * 2.0;
}
```
不加这条，机器人启动时会被刚性冲击掀翻（仿真中倾角 179° → 加后 <31°）。

### 4.7 多输入族（F）的 `command`

- `uncertain` 恒为 **1.0**
- `command[1,N]` 由 `updateCommand → cal_command(robotState, userCommand, …)` 计算，`command_dim` = **21**（FinetuneStand/SixAxis）、**13**（StepMove）、**5**（Extre）
- 仿真实测 `command[0] = v_x` 即可驱动 `forward_policy_2` 以 ~0.72 m/s 前进
- **二次开发提示**：若要完整复刻，需逆向 `cal_command`（含 `gait_w`、`half_gait_T`、加速度限幅等），函数地址与 `updateCommand` 各 runner 内均可定位

---

## 5. ★ 数字孪生使用说明

### 5.1 环境

```bash
# Python 环境（已就绪）
/home/lee/rea/venv/bin/python        # mujoco 3.16, onnxruntime 1.23, pyelftools
# 系统
ROS 2 Humble + Gazebo 11.10.2 + GTSAM 4.2 + ros2_control  # /opt/ros/humble
```

### 5.2 快速开始

```bash
cd /home/lee/rea

# 1) 模型自检（16 自由度 / 限位 / 质量 / 稳定性）
./venv/bin/python sim/validate_model.py

# 2) 策略可执行性 + 关节标定校验
./venv/bin/python sim/replay_eval.py

# 3) ★ 用真实部署权重跑站立（10 秒）
./venv/bin/python sim/sim2sim_deployed.py \
    bin/policies/policy_policy_m20_50.onnx 10 0 M20BasicFlatRunner

# 4) ★ 行走（vx=0.5 m/s）
./venv/bin/python sim/sim2sim_deployed.py \
    bin/policies/policy_policy_m20_50.onnx 10 0.5 M20BasicFlatRunner
```

**脚本参数**：`<policy.onnx> <duration_s> <vx> <runner_name> [gait_freq]`
输出：高度 z、倾角 tilt、终点 xy、HELD/FELL 判定 + 时间序列。

### 5.3 回归全部策略

```bash
# 参考 sim/deployed_regression.md 中的命令矩阵；示例：
for pair in \
  "policy_policy_m20_50:M20BasicFlatRunner" \
  "policy_policy_ca9bplatform:M20BasicPlatRunner" \
  "policy_m20_navi_flat_v4_2:M20NaviFlatPolicyRunner" \
  "policy_m20_flat_v1_4:M20StandPolicyRunner" \
  "policy_m20_forward_policy_2:M20ExtrePolicyRunner" \
  "policy_m20_hmap_motion_v0_2:M20HeightGapPolicyRunner" ; do
  pol=${pair%%:*}; run=${pair##*:}
  ./venv/bin/python sim/sim2sim_deployed.py bin/policies/$pol.onnx 10 0 "$run" | grep -E "HELD|FELL"
done
```

### 5.4 接入你自己的控制器（二次开发主路径）

`sim/sim2sim_deployed.py` 是**规格驱动**的，三个切入点：

1. **换策略**：把任意 ONNX 放到 `bin/policies/`，按 §4 契约喂观测、取动作
2. **改规格**：编辑 `RUNNER_SPEC`（order/gait/pre/post/hmap）即可适配新的观测布局
3. **换控制器**：跳过 ONNX，直接把 `goal_pos`/`goal_vel` 换成你自己的 PD/MPC 输出——
   MuJoCo 侧只需 `d.ctrl[:] = clip(kp*(goal_pos−q) + kd*(goal_vel−v), −80, 80)`

```python
# 最小骨架（在自己脚本里复用）
import mujoco, numpy as np
m = mujoco.MjModel.from_xml_path("sim/m20_description/mjcf/M20.xml")
m.opt.timestep = 1e-3
d = mujoco.MjData(m)
# 初始站立位（MJCF = 发布域）
DEFAULT = [-0.1,-0.8,1.6, 0.1,-0.8,1.6, -0.1,0.8,-1.6, 0.1,0.8,-1.6]
jid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n+"_joint") for n in ROBOT_ORDER]
for leg in range(4):
    for j in range(3):
        d.qpos[m.jnt_qposadr[jid[leg*4+j]]] = DEFAULT[leg*3+j]
d.qpos[2] = 0.45; d.qpos[3] = 1.0
mujoco.mj_forward(m, d)
```

### 5.5 模型资产

| 文件 | 说明 |
| --- | --- |
| `sim/m20_description/mjcf/M20.xml` | MJCF 主模型（16 关节，总质量 34.526 kg）|
| `sim/m20_description/urdf/m20.urdf` | 导出的 URDF（17 link / 16 joint，`check_urdf` 通过）|
| `sim/m20_description/calibration.json` | 关节方向/零位/缩放系数表 |
| `sim/m20_description/meshes/` | 17 命名 STL + 2202 编号 STL |

> 常用传感器取数：`d.sensordata[0:4]`=base_quat，`[4:7]`=加速度，`[7:10]`=陀螺。

---

## 6. 协议与上位机二次开发

### 6.1 话题/服务（实测 98 话题 / 30+ 服务）

| 用途 | 话题/服务 |
| --- | --- |
| 传感器 | `/LIDAR/POINTS`(10Hz)、`/IMU_YESENSE`(200Hz)、`/BATTERY_DATA`、`/GPS` |
| 运控 | `/JOINTS_DATA`、`/JOINTS_CMD`、`/MOTION_STATUS`、`/GAIT`、`/MOTION_INFO`、`/STEER` |
| 状态估计 | `/LIO_ODOM`、`/LIO_ODOM_HIGH_FREQUENCY`、`/ODOM`、`/LOCATION_STATUS` |
| 导航 | `/GRID_MAP`、`/NAV_POINTS`、`/path_Astar`、`/local_goal`、`/planner_mode`、`/NAV_CMD`、`/GLOBAL_PLANNER_STATUS` |
| 服务 | `/GOAL_GLOBAL`、`/CANCEL_NAV_GLOBAL`、`/SDK_MODE`、`/LIO_ENABLE`、`/HEIGHT_MAP_ENABLE`、`/encryptionCheck`、`/CHARGE` |

完整表：`analysis/03_middleware_dds.md`；消息 schema：`analysis/13_drdds_messages.md`。

### 6.2 自定义 drdds 消息（二次开发注意）

原厂用 `drdds` 包（非标准 ROS 消息），**必须链接 `libdrdds.so.1`**（`/usr/local/lib`）才能收发；CDR 编码，4 字节封装头。解码参考 `decoders/drdds_decoder.py`、`decoders/rosbag_odom_decoder.py`。

### 6.3 只读连接实机

```bash
cd /home/lee/rea
./dogssh.sh 10.21.41.1 "uname -a"        # 密码式 SSH（AOS）
./dogsudo.sh "your command"              # 带 sudo
./dog.sh "ros2 topic list"               # 需先 sourc 环境
```
> 安全约束：机器狗保持趴下；只读；禁止写盘、停服务、刷固件、带电探针、
> 对运控进程用 `strace/gdb/perf`。凭据在 `QUARANTINE/`，勿外发。

---

## 7. 建图 / 导航二次开发

### 7.1 建图（FAST-LIO 系）

- 算法：LiDAR-惯性紧耦合 **IEKF on manifold**（IKFoM），23 维状态；后端 GTSAM/iSAM2 位姿图 + ScanContext/GHT 回环
- 源码级参照：`dump/hostA/home_user/m20_orignal/`（完整可编译工程）
- 本地工作区：`sim/ws/src/m20_slam_navigation/`（已编译，7/7 测试通过）
```bash
cd sim/ws && source /opt/ros/humble/setup.bash
colcon build --packages-select m20_slam_navigation --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
ctest --test-dir build/m20_slam_navigation --output-on-failure
```
- 实机 281m 走航数据：`captures/bag/20260916/db3/`（451 帧 96 线点云 + 452 帧 /ODOM）
- 评测：`./venv/bin/python sim/mapping_eval.py`
- 注意：配置里 LiDAR-IMU 外参为**单位阵**（雷达驱动已做安装变换）；`lio_ddsnode` 已剥离符号，与开源 FAST-LIO 的差异需行为级验证

### 7.2 导航（Hybrid A* + DWA/LinePlanner）

| 组件 | 参数文件 | 要点 |
| --- | --- | --- |
| 全局 | `dump/hostC_opt_robot/config/config_astar.yaml` | 加权 A*（`weight_a=1.0, weight_b=1.3`）、`step_size=0.4`、三次样条平滑（`smooth_count=7, degree=3`）|
| 局部 | `dump/hostC_opt_robot/config/localplanner.yaml` | DWA/LinePlanner 双模、`maxSpeedX=1.5`、`stop_distance=0.7`、DWA 权重 `1.0/0.5/0.2 + 0.6/0.8/1.0`、轨迹库 `path_num=4641` |
| 速度档位 | AOS `basic_server.toml` | FLAT/STAIR/ORIENTEER × LOW/NORMAL/HIGH 覆盖 `stop_distance` 0.6–1.3 |

- 闭环评测：`sim/nav_sim/nav_closed_loop`（源码 `sim/nav_sim/nav_closed_loop.cpp`）
```bash
cd sim && ./nav_sim/nav_closed_loop            # 3 场景：直线/斜向/绕障
```
- 详细报告：`analysis/19_navigation_T26_deep.md`、`sim/nav_sim_report.md`

---

## 8. 二次开发建议路线

| 目标 | 建议起点 | 备注 |
| --- | --- | --- |
| 自研运控策略 | §4 契约 + `sim/sim2sim_deployed.py` | 观测/动作已完全明确，可直接训练→ONNX→同规格接入 |
| 策略微调 / 域随机化 | 同上 + `sim/ws` | 训练端奖励函数未逆向，需自行设计 |
| 新导航算法 | `sim/ws/src/m20_slam_navigation` | 保持原厂话题名即可与实机对接 |
| 上位机 App | `analysis/04_protocols.md` §② | App 帧 `0xEB90EB90` + JSON `PatrolDevice{Items,Type,Command}` |
| 手柄接管 | `04_protocols.md` §① + `/SDK_MODE` 服务 | 手柄 UDP 12121，`0x55 0x66` + CRC16 |
| 实机部署 | 需先完成 L3（吊架安全基准）| 当前仅只读授权 |

### 已知边界（做二次开发前必读）

1. **ECAN 底层**：CAN-FD 帧格式在 `libecanmaster.so` 内，未逐字节还原；直读电机固件需 SWD（L3）
2. **`cal_command`**：多输入族的 `command` 完整语义未逆向（仅知 `command[0]=v_x` 有效）
3. **训练端**：奖励函数、域随机化、课程学习未逆向
4. **`NaviCharge`**：构成与软启动已全解，但作为充电位对接策略，零指令下持续移动
5. **`lio_ddsnode` 已剥离**：与开源 FAST-LIO 的私有差异（深度图补坑、环视点云 UDP、多分辨率高程图）为行为级验证

---

## 9. 证据与复现

### 9.1 实时核验（`analysis/23_live_verification.md`）

8 个关键二进制/固件与实机**哈希逐一字节一致**：`rl_deploy`、`basic_server`、`lio_ddsnode`、`astar_node`、`localPlanner`、`localization_ddsnode`、`handler`、`ecan_V2.0.15.bin`。
→ 所有静态结论均对应当前实机固件。

### 9.2 反编译留档（`notes/`）

| 文件 | 内容 |
| --- | --- |
| `ghidra_lio_extrinsic.txt` | LIO 外参读取路径 |
| `ghidra_rl_obs.txt` | 观测拼装 + 关节序 |
| `ghidra_rl_allctors.txt` | 14 个 runner 构造函数全部参数 |
| `ghidra_extra_obs.txt` | NaviCharge/NaviFlat/StandPolicy 观测 |
| `ghidra_multi_obs.txt` | 多输入族 + gait_switching_logic |
| `ghidra_updatecmd.txt` | updateCommand 实现 |
| `ghidra_policy_map.txt` | 策略↔runner 映射 |

### 9.3 复现脚本（`tools/`）

```bash
export GHIDRA_INSTALL_DIR=/opt/ghidra_12.1.4_PUBLIC
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
./venv/bin/python tools/ghidra_rl_obs.py        # 反编译观测构建函数
./venv/bin/python tools/ghidra_policy_map.py    # 策略↔runner 映射
./venv/bin/python tools/parse_runner_params.py  # 解析 runner 参数表
./venv/bin/python tools/ghidra_lio_extrinsic.py # LIO 外参
```

---

## 10. 状态与验收

| 验收项 | 标准 | 结果 |
| --- | --- | --- |
| L1-① 链路清单 | 4 条链路物理/协议/端口/频率齐全 | ✅ |
| L1-② 帧解码率 | ≥95% | ✅ |
| L1-③ FSM 对应 | DWARF 枚举 + 运行时日志双证 | ✅ |
| L1-④ RL 观测/动作 | 逐维还原 | ✅（7 变体）|
| L1-⑤ 建图 ATE / 导航偏差 | <0.1m / <0.3m | ✅（仿真重建；实机数据 281m 已备）|
| L2-① URDF 加载 | 关节/轮数限位与实机一致 | ✅ |
| L2-② 策略回放误差 | <5% | ✅ |
| L2-③ 仿真站立 30s + 行走 | 不倒 | ✅ |
| **实机部署权重闭环** | 15 策略 | **14/15 站走通过** |

---

_本文档随成果更新。所有数字均来自实机或二进制证据，未经验证的推测均已标注。_
