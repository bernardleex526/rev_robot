# 云深处 M20 Pro 逆向成果 — 核验结论与 WSL 二次开发技术文档

> 对象仓库：`https://github.com/bernardleex526/rev_robot`（单提交 `44dabbe3`），本地 `E:\ccmax\rev_robot`
> 核验日期：2026-10-16　核验环境：Windows 11 + WSL2 Ubuntu 22.04（ROS 2 Humble、8 核、7 GB）
> 方法：在 WSL 中实际复跑仓库脚本、编译工程、核对 Ghidra 反编译笔记与二进制哈希、逐篇交叉比对文档。仓库本身未做任何修改。
> 配套脚本：`E:\ccmax\rev_robot\m20_wsl_scripts\`（00/01/02 均已从零实跑通过）

---

## 0. 一页结论

| 维度 | 结论 |
| --- | --- |
| **整体可用性** | **高。** 静态证据链完整：8 个关键二进制与实机哈希一致；官方 SDK、MJCF 模型、15 个部署策略、drdds 消息定义齐全。WSL 下可直接开展仿真与算法测试。 |
| **最重要的新增结论** | 用 dump 出的 `.msg/.srv` **能在 Humble 下重建 `drdds` 接口包**，官方 SDK 的 `rl_deploy` 能编出 x86 版，并与 MuJoCo 经 DDS 闭环跑通（`/JOINTS_CMD`、`/JOINTS_DATA`、`/IMU_DATA` 约 200 Hz）。原仓库文档没有给出这条路径。 |
| **文件齐全性** | 缺 3 类：①录包 `.db3` 和 `20260916_db3.tar.bz2`（LFS，下载中或失败）；②GOS（104）主机零 dump；③SDK 授权文件、地图 `full_cloud.pcd`/`occ_grid.yaml` 未拉取。另有 4,985 个 dpkg 元数据文件因含 `:` 在 Windows 上无法检出，无影响。 |
| **正确性** | 主体正确，但有**多处需修正的错误或过时结论**，见 §2。其中三条会直接误导二次开发：①策略↔runner 映射有一对写反；②`kp/kd` 表和 `runner_params.json` 有误；③"281 m 实机走航数据"基本可判定为假象。 |
| **安全** | 仓库根目录 `dogssh.sh`、`dogsudo.sh`、`rsudo.sh`、`env.sh` 含**明文 SSH/sudo 密码**，且仓库公开。建议立即轮换并从历史中清除。 |

---

## 1. 齐全性核查

### 1.1 克隆与检出状态（Windows 特有问题）

| 项 | 情况 | 处理建议 |
| --- | --- | --- |
| `dump/hostA/opt_robot/.dpkg/info/*:arm64.*`（4,985 个） | 文件名含 `:`，NTFS 不允许，未检出 | 只是 dpkg 安装清单，不影响开发。需要时在 WSL 原生文件系统重新克隆：`cd ~ && git clone …` |
| LFS 大文件 4 个（共约 1.4 GB） | `lio_ddsnode_ghidra/db.3.gbf` 已到；`rl_deploy_ghidra/db.15.gbf`(687 MB)、`JOINTDAMPING_…_0.db3`(443 MB)、`20260916_db3.tar.bz2`(261 MB) 因 GitHub 超时未到 | 在 WSL 内执行 `git lfs pull`，网络慢时可加代理。缺少这些文件时，录包分析和 rl_deploy 的 Ghidra 工程无法打开，其余不受影响 |
| `QUARANTINE/`、`venv/` | `.gitignore` 有意排除 | `venv` 用 `00_setup_python_venv.sh` 重建 |
| `sim/ws/build`、`sim/ws/install` | 过期构建产物，含 `/home/lee/rea` 绝对路径（约 48 MB） | 忽略，只用 `sim/ws/src` 重新编译 |

> **强烈建议在 WSL 原生文件系统（`~/`）重新克隆一份作为开发主副本。** 这样能检出全部文件（含 `:` 名），也不会有 CRLF 换行问题，编译速度也远快于 `/mnt/e`。

### 1.2 资产清单（存在 ✅ / 缺失 ❌）

| 资产 | 位置 | 状态 |
| --- | --- | --- |
| 运控主程序 `rl_deploy`（aarch64，含 DWARF，94.5 MB） | `bin/`、`dump/hostA/opt_robot/share/rl_deploy/bin/` | ✅ 哈希 `59aa77a2…` 与实机一致 |
| `basic_server` / `lio_ddsnode` | `bin/` | ✅ 哈希一致 |
| NOS：`astar_node` / `localPlanner` / `localization_ddsnode` / `handler` | `dump/hostC_opt_robot/bin/` | ✅ 哈希一致（aarch64） |
| ECAN 固件 `ecan_V2.0.15_*.bin`、`libecanmaster.so` | `dump/hostA/opt_robot/share/ecan_master/`、`…/lib/` | ✅ |
| 15 个部署策略 ONNX | `bin/policies/` | ✅ 全部可加载（ir8 / opset17） |
| 官方 SDK `M20_sdk_deploy`（含 x86 onnxruntime、MJCF、`policy.onnx`） | `dump/hostA/home_user/sdk_deploy/src/M20_sdk_deploy/` | ✅ **x86 可编译**（见 §3.3） |
| drdds 消息定义（60 msg + 8 srv + Foxy 生成的 idl） | `dump/hostA/ros_foxy_share/` | ✅ 可重建（文档写 44 个，实为 60 个） |
| drdds C++ 头文件（FastDDS 生成，766 个） | `dump/hostA/usr_local_include/dridl/` | ✅ |
| `libdrdds.so.1.1.7` | `bin/` | ✅ 但为 aarch64，x86 不可用，需用 IDL 重建 |
| MJCF 模型 + 2202 个 STL | `sim/m20_description/` | ✅ 与官方 SDK 逐字节一致 |
| URDF | `sim/m20_description/urdf/m20.urdf` | ⚠️ 存在但**无 visual/collision**，不可直接用于 Gazebo/Isaac |
| SLAM/导航重建工程 | `sim/ws/src/m20_slam_navigation`、`dump/hostA/home_user/m20_orignal/` | ✅ 可编译，7/7 测试通过；**是第三方行为级重建，非原厂源码** |
| LIO / 导航 / basic_server 配置 | `…/lio-perception/conf/params.yaml`、`dump/hostC_opt_robot/config/*.yaml`、`basic_server.toml` | ✅ |
| 抓包 pcap（2 个）、CSV 快照 | `captures/` | ✅ |
| 录包 db3 本体 | `captures/bag/20260916/db3/…` | ❌ 仅 `metadata.yaml`（LFS 未到） |
| GOS（104）文件系统 | — | ❌ 只有 `runtime/hostB_104_*.txt` 三份勘测输出 |
| SDK 授权 `SDK_authority_code.toml` | — | ❌ 未拉取（SN 绑定）。**没有它实机无法进入 SDK 接管模式** |
| 地图 `full_cloud.pcd`、`occ_grid.yaml` | — | ❌ 未拉取 |
| 全盘镜像 | `/media/lee/数据/rea_images/`（作者本机） | ❌ 不在仓库 |
| USD / xacro | — | ❌ 不存在 |

---

## 2. 正确性核查：需修正的结论

判定依据都是仓库内证据，并已在 WSL 复现。按对二次开发的影响排序。

### 2.1 高影响（会直接导致结果错误）

| # | 原结论（出处） | 实际情况（证据） |
| --- | --- | --- |
| 1 | `finetune_stand_15kg → FinetuneStandRunner`，`sixaxis_stand → SixAxisStandRunner`（`DEVELOPER_GUIDE.md` §4.1） | **写反了。** `notes/ghidra_policy_map.txt:8,13`：`sixaxis_stand → M20FinetuneStandRunner`，`finetune_stand_15kg → M20SixAxisStandRunner`。`sim/deployed_regression.md` 的表是对的 |
| 2 | Navi* 的 `kp=80, kd=3`；StandPolicy 的 `kd=[2,2,2,0.6]`（DG §4.5） | Ghidra（`notes/ghidra_rl_allctors.txt`）显示：<br>- NaviFlat/NaviOrienteer/NaviCharge：kp `[60,60,60,0]`、kd `[1.5,1.5,1.5,0.6]`<br>- BasicFlat：kd **`[6,6,6,0.6]`**（:290）<br>- BasicPlat/StandPolicy：kp `[80,100,100,0]`、kd `[2.5,2.5,2.5,2.0]`（:500、:3019）<br>- HeightGap：kp `[80,80,120,0]`、kd `[3,3,4,0.6]`<br>- 多输入族（Extre/FinetuneStand/SixAxis/StepMove）：kp 60 |
| 3 | `sim/runner_params.json` 是"逐 runner 真值" | 其 `kp/kd` 字段是**解析错误的数据**（例如 BasicFlat 的 kp 为 8 个标量 `[0,6,6,6,0.6,2,1,2]`）。仿真脚本没有使用这两个字段，而是用硬编码的 KP=80/KD=3。**不要把这些字段当真值** |
| 4 | `sim2sim_deployed.py` 的全局 `WHEEL_VEL_SCALE=0.05`（:31） | 基类应为 **0.01**（`notes/ghidra_rl_ctor.txt:81`）。脚本只在 json 有值时覆写（:92），没有覆写字段的 runner 因此被错误地用了 0.05。改成 0.01 后：StandPolicy 行走从 **FELL** 变为 HELD（5.07 m），Plat 和 NaviFlat 的行走距离从约 2 m 增至约 5–6 m。多输入族为 0.0333，Basic*/NaviStair 为 0.05 |
| 5 | "14/15 策略站走通过"，flat_v1_4 行走 ✅（`deployed_regression.md`） | 原样复跑时 flat_v1_4 在 vx=0.5 下 **FELL**（倾角 176°），修正上面第 4 条后才通过。NaviCharge 站立和行走均 FELL，是**确定的唯一失败项**，根因未明 |
| 6 | "实机 bag 含 281.85 m 连续走航，平均 6.46 m/s、最高 12.79 m/s"（STATUS、DG §7.1、`mapping_sim_report.md`） | **基本可判定为假象。** 依据：<br>①bag 名为 `JOINTDAMPING_*`，即泄力状态；<br>②同时段 CSV（8411 行、42 s）中状态恒为 4、Steer 全为 0、IMU `acc_z≈9.85`（标准差 0.013）、`|ω_z|<0.016`，说明机器人静止；<br>③12.79 m/s 约 46 km/h，物理上不可能。<br>很可能是 `/ODOM` 漂移、坐标系或单位问题。**不要用它评估 SLAM** |

### 2.2 中影响（文档过时或自相矛盾）

| # | 问题 | 正确值 / 位置 |
| --- | --- | --- |
| 7 | 总线写作 EtherCAT | 应为 **CAN-FD over Ethernet**（`libecanmaster.so`）。未改的有 `analysis/02:29`、`04:118`、`09:25`、`11:17`、`14:32`、`15:80`、`16:19`、`20:12` |
| 8 | 调度写作 SCHED_FIFO | `rl_deploy` 进程为 **SCHED_RR 90**、CPU 4,5（`23:57`）。`06:52`、`14:32` 未改；`04:73` 是 ecan 线程构造参数，与进程级调度不同 |
| 9 | `decimation=4`、5 ms 周期 | 这是 **SDK 版**的值。部署版 `decimation_=20`（`ghidra_rl_ctor.txt:75`），主循环 1 kHz、策略 50 Hz。05、06、14、20 混用了两者 |
| 10 | `kRLControl (6)`（`05_fsm_motion.md:54`） | 部署版为 **17**（`bin/rl_deploy_enums.txt:68`），SDK 版为 6 |
| 11 | "12 态" | 有效状态 11 个，加上 `kInvalid=-1` 才是 12 个；步态 20 个正确 |
| 12 | 网络 "57→512→256→128→16"（L1、06） | 这是 SDK 的 `policy.onnx`（输入 `obs[57]`）。部署策略为 `state[318]`（53×6）→ `output[16]` + `vel[3]` |
| 13 | 话题数 98 / 170 | `runtime/hostA_dds.txt` 实为 106 话题 + 57 服务 + 4 节点 |
| 14 | `ca9bplatform` ❌（`24` §5） | 已过时，实测 HELD |
| 15 | 2202 个 STL 都是机器人网格 | 机器人只用 17 个命名 STL；其余 2185 个编号 STL 仅被 `scene.xml` 引用，是**场景/楼梯环境** |
| 16 | 协议解码率 ≥95% | 只在**帧结构层**成立（RTPS 97.6%，CDR 封装头 100%）。字段语义层没有建立 topic→type 映射，312/404 字节族与 schema 尺寸对不上 |
| 17 | 建图 ATE<0.1 m、导航偏差<0.3 m ✅ | 仅为**自写运动学仿真中的自洽验证**，不是实机或原厂行为对比 |
| 18 | `handler_*.yaml` 的 `maxSpeedX=2.0` | DG 只引用了 localplanner 的 1.5，两者不同 |

### 2.3 核验为正确的关键结论（可放心使用）

- 三主机拓扑（103 AOS / 104 GOS / 106 NOS）、Ubuntu 20.04.6 aarch64、内核 5.10.198、ROS 2 Foxy + Fast DDS 2.14。
- 8 个关键二进制 SHA-256 与 `analysis/23` 逐一相符（本次重算）。
- 15 个 ONNX 的输入形状与 7 种观测变体完全对应：
  - A/B = 318（53×6）
  - D = 324（54×6）
  - C = 360（60×6）
  - E = 366（61×6）
  - G = 3024（504×6）
  - F = `state[1,36,53]` + `command[1,N]` + `uncertain[1,1]`，N = 5（forward_policy_2）、13（finetune_forward）、21（finetune_stand_15kg、sixaxis_stand）
- 基类常量 `obs_dim_=53`、`decimation_=20`、`wheel_vel_scale_=0.01`、`action_scale_=0.25`、`wheel_action_scale_=10`（多输入族 20）。
- FSM 枚举值（除 05:54 笔误外）、20 种步态。
- MJCF：总质量 34.526 kg；16 个 `<motor>` 力矩执行器（腿 ±76.4、轮 ±21.6 N·m）；`sensordata[0:4]` 为四元数，`[4:7]` 为加速度，`[7:10]` 为陀螺。
- drdds 关键消息（JointsData/JointsDataCmd/ImuData/MotionStatus/NavCmd/Gait/MotionInfo/Steer）与 `13_drdds_messages.md` 一致。
- LiDAR-IMU 外参在 LIO 中为单位阵，雷达安装（x=±0.32028）由 rslidar 驱动处理。
- 导航参数（`weight_a=1.0, weight_b=1.3, step_size=0.4, maxSpeedX=1.5, stop_distance=0.7, path_num=4641`）与原厂配置一致。

---

## 3. WSL 开发环境搭建（全部已实测）

### 3.1 前提

- WSL2 Ubuntu 22.04 + ROS 2 Humble（`/opt/ros/humble`）、g++、cmake、colcon。本机已具备。
- 若需 GUI（MuJoCo viewer），Windows 11 自带 WSLg 即可。

### 3.2 Python 仿真环境

```bash
bash /mnt/e/ccmax/rev_robot/m20_wsl_scripts/00_setup_python_venv.sh
# 得到 ~/.venvs/m20：mujoco 3.16、onnxruntime 1.23、onnx、numpy、scipy、rosbags、scapy
```

### 3.3 ★ 重建 drdds + 编译官方 SDK（x86）

```bash
REPO=/mnt/e/ccmax/rev_robot W=~/m20_ws bash /mnt/e/ccmax/rev_robot/m20_wsl_scripts/01_build_drdds_and_sdk.sh
```

脚本做了这些事：

1. 从 `dump/hostA/ros_foxy_share/{msg,srv}` 生成 `drdds` 的 `CMakeLists.txt`，依赖 `builtin_interfaces` 和 `geometry_msgs`（`JudgeVel.srv` 用到 `Twist`）。
2. 删除 Foxy 生成的 `.idl`，由 Humble 的 rosidl 重新生成。
3. 用 `-DBUILD_PLATFORM=x86` 编译官方 `m20_sdk_deploy`。它唯一缺的系统库是 `libevdev-dev`：有 sudo 就 `apt install`，没有则由脚本把 deb 解到本地。

结果：`drdds` 约 50 s，SDK 约 45 s；Python 可 `from drdds.msg import JointsData`。

### 3.4 ★ 官方 SDK sim-to-sim（MuJoCo ↔ rl_deploy）

```bash
# 无头冒烟测试（已实测 /JOINTS_DATA ≈175 Hz、/JOINTS_CMD ≈200 Hz、/IMU_DATA ≈180 Hz）
bash /mnt/e/ccmax/rev_robot/m20_wsl_scripts/02_sdk_sim2sim_headless.sh

# 交互（WSLg 图形界面），两个终端：
cd ~/m20_ws && source install/setup.bash && export ROS_DOMAIN_ID=1
ros2 run m20_sdk_deploy rl_deploy                                     # 终端 1
python3 src/M20_sdk_deploy/interface/robot/simulation/mujoco_simulation_ros2.py   # 终端 2
# 终端 2 的 Python 需能 import mujoco 和 scipy，可执行：
#   export PYTHONPATH=$PYTHONPATH:$(~/.venvs/m20/bin/python -c 'import site;print(site.getsitepackages()[0])')
# 键位：z 站立，c 进 RL，wasd 平移，qe 转向
```

这条链路使用**与实机相同的话题名和 drdds 消息类型**，是将来 sim-to-real 的最短路径。注意：SDK 用的是 57 维 SDK 策略，不是 15 个部署策略。

### 3.5 仓库自带的数字孪生（部署策略回放）

```bash
mkdir -p ~/m20_twin/bin ~/m20_twin/captures/csv/20260916/csv
cp -r /mnt/e/ccmax/rev_robot/sim ~/m20_twin/ && cp -r /mnt/e/ccmax/rev_robot/bin/policies ~/m20_twin/bin/
cp /mnt/e/ccmax/rev_robot/captures/csv/20260916/csv/snapshot_20260916_191124.csv ~/m20_twin/captures/csv/20260916/csv/
cd ~/m20_twin && PY=~/.venvs/m20/bin/python
$PY sim/validate_model.py          # 模型自检，全部 PASS
$PY sim/replay_eval.py             # 15/15 可执行，标定往返误差 4e-16
$PY sim/sim2sim_deployed.py bin/policies/policy_policy_m20_50.onnx 10 0.5 M20BasicFlatRunner
```

- 参数格式：`<onnx> <秒> <vx> <Runner> [gait_freq]`。脚本用 `Path(__file__)` 定位，**无需改路径**。
- **使用前务必修正**：把 `sim/sim2sim_deployed.py:31` 的 `WHEEL_VEL_SCALE` 改为 `0.01`；按 §2.1 第 2 条修正各 runner 的 kp/kd（脚本里的 `OVERRIDE`）。
- 当前孪生对 kd 不敏感，"能站住"不等于参数正确。

### 3.6 SLAM / 导航重建工程

```bash
mkdir -p ~/m20_nav/ws && cp -r /mnt/e/ccmax/rev_robot/sim/ws/src ~/m20_nav/ws/
cd ~/m20_nav/ws && source /opt/ros/humble/setup.bash
colcon build --parallel-workers 4 --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON   # ~2.5 min
ctest --test-dir build/m20_slam_navigation --output-on-failure                                    # 7/7 通过

# 导航闭环仿真（Hybrid A* + DWA，3 场景 ALL PASS）
cd ~/m20_nav && cp -r /mnt/e/ccmax/rev_robot/sim/nav_sim . && B=ws/build/m20_slam_navigation
g++ -std=c++17 -O2 nav_sim/nav_closed_loop.cpp -o nav_sim/ncl \
  -Iws/src/m20_slam_navigation/include -I/usr/include/eigen3 -I/usr/include/pcl-1.12 \
  -I/opt/ros/humble/include -L$B -lm20_slam_core -Wl,-rpath,$PWD/$B && ./nav_sim/ncl
```

- 依赖 GTSAM、PCL 1.12、gtest，Humble 环境已齐全。
- 不要运行仓库里提交的 `nav_sim/nav_closed_loop` 二进制，从源码重编。

---

## 4. 机器人技术规格速查（已核验）

### 4.1 系统

| 项 | 值 |
| --- | --- |
| 机型 | 云深处 CA9B / M20 Pro，轮足四足，16 DoF（12 关节 + 4 轮） |
| 计算 | 3× aarch64（8×A55, 16 GB）：AOS 10.21.31.103（Wi-Fi 10.21.41.1）、GOS .104、NOS .106 |
| 软件 | Ubuntu 20.04.6、ROS 2 Foxy、Fast DDS 2.14.2、裸 DDS 参与者（`ros2 node list` 看不到业务节点） |
| 运控 | `rl_deploy`：FSM + ONNX 策略，1 kHz 主循环、策略 50 Hz，SCHED_RR 90 |
| 电机总线 | ECAN = CAN-FD over Ethernet（`eth1`，`libecanmaster.so`） |
| 传感器 | 双 Robosense Airy（UDP 6691/6692 → `/LIDAR/POINTS` 10 Hz）、Yesense IMU（`/dev/ttyS9` → `/IMU_YESENSE` 200 Hz） |

### 4.2 关节约定

```
机器人序（16）: [FL(hipx,hipy,knee,wheel), FR, HL, HR]
关节主序（12）: [hipx×4, hipy×4, knee×4]      腿主序（12）: [FL3, FR3, HL3, HR3]
默认站姿（MJCF=发布域）: 前腿 (-0.1,-0.8,1.6)/(0.1,-0.8,1.6)，后腿 (-0.1,0.8,-1.6)/(0.1,0.8,-1.6)
```

关节限位（rad）：

| 关节 | 限位 | 轴 |
| --- | --- | --- |
| hipx | fl/hl [-0.436, 0.611]；fr/hr [-0.611, 0.436] | (-1,0,0) |
| hipy | 前 [-2.286, 2.583]；后 [-2.583, 2.286] | (0,-1,0) |
| knee | 前 [-2.809, 2.792]；后 [-2.792, 2.809] | (0,-1,0) |
| wheel | 连续 | (0,-1,0) |

### 4.3 部署策略观测（基础 53 维 / 帧）

```
ω_body×0.25 (3) | 投影重力 (3) | cmd×[1,1,0.25] (3) | dof_pos−default (12) | dof_vel×0.05 (12)
| wheel_vel×wheel_vel_scale (4) | last_action (16)
历史：[当前帧 | 5 帧历史] = 6 帧 → 318；F 族为 36 帧整段
动作：goal_pos = act×0.25 + default；goal_vel(wheel) = act×10（多输入族 20）；act 先钳位 ±100
力矩：tau = kp(goal_pos−q) + kd(goal_vel−q̇)
```

各变体（A–G）的插入项见仓库 `DEVELOPER_GUIDE.md` §4.2；该节正确。kp/kd 以本文 §2.1 第 2 条为准。

### 4.4 关键话题与消息（drdds）

| 话题 | 类型 | 说明 |
| --- | --- | --- |
| `/JOINTS_DATA` | `drdds/JointsData` | 16 关节状态 |
| `/JOINTS_CMD` | `drdds/JointsDataCmd` | 关节指令；约 100 ms 不更新即转入 JointDamping |
| `/IMU_DATA`（SDK）/ `/IMU_YESENSE`（实机） | `drdds/ImuData` | rpy、ω、acc |
| `/NAV_CMD` | `drdds/NavCmd` | x_vel、y_vel、yaw_vel |
| `/ODOM`、`/LIO_ODOM` | `nav_msgs/Odometry` | — |
| `/SDK_MODE`（服务） | `StdSrvInt32` | 200 = 进入 200 Hz SDK 模式，0 = 退出；需 SN 绑定授权 |

---

## 5. 二次开发路线建议

| 目标 | 推荐路径 | 注意 |
| --- | --- | --- |
| **新运控策略（RL）训练与测试** | 在 Isaac Lab / legged_gym 训练，按 §4.3 契约导出 ONNX，先在 §3.5 的孪生回放，再接 §3.4 的 SDK 链路 | 训练端奖励和域随机化未逆向，需自行设计；MJCF 无关节阻尼/电枢，sim2real 需补电机模型 |
| **传统控制（MPC/WBC）** | 在 §3.4 的 SDK 框架里替换 `run_policy/` 里的策略执行器，直接发 `/JOINTS_CMD` | 执行器是纯力矩，ctrlrange 腿 ±76.4、轮 ±21.6 |
| **导航/规划算法** | `sim/ws/src/m20_slam_navigation`（已编译通过），保持原厂话题名 | 它是行为级重建，结论需上机验证 |
| **SLAM 算法** | 同上 + 补齐 LFS 录包 | 不要用 JOINTDAMPING 包做精度评估（见 §2.1 第 6 条）；需重新录制真实行走数据（含 IMU） |
| **Gazebo / Isaac 仿真** | 先修 `sim/mjcf_to_urdf.py` 再生成 URDF | 当前 URDF 无几何体；轮子应改 `continuous`；需保留惯量主轴；Isaac 需从 URDF 转 USD |
| **上位机/App** | `analysis/04_protocols.md` §②，必要时 JADX 反编译 `sdk/controlapp.apk` | App 命令集只有 3 条，`apk_package.json` 只是元数据 |
| **实机联调** | WSL 需 `networkingMode=mirrored`（`.wslconfig`），或在 Fast DDS 配置单播 initial peers；domain 0；Humble 与 Foxy 线上互通 | 需 `SDK_authority_code.toml`（不在仓库）；原 `fastdds.xml` 的 interfaceWhiteList 写死了机内 IP，不能直接复用；首次务必吊架 |

### 已知未解问题

1. **NaviCharge** 策略在孪生中站立即倒，根因未明（wheel_vel_scale 已排除，疑为相位初值、软启动或 kp/kd）。
2. **多输入族的 `cal_command`** 语义未逆向，目前只知 `command[0]=v_x` 有效。
3. **ECAN CAN-FD 帧与 CRC（`CalCRCEPht`）**、手柄/MCU 的 CRC16 多项式未给出，也无线上抓包。
4. 解码器依赖 `tshark`（`sudo apt install tshark`）。`drdds_decode.py` 硬编码了 `/home/lee/rea`。
5. `rough_6`、`m20_38` 两个策略没有 runner 交叉引用，其 runner 归属是推测。
6. `lio_ddsnode` 已剥离符号，与开源 FAST-LIO 的私有差异仅为行为级推断。

---

## 6. 建议对原仓库做的修正（按优先级）

1. **安全**：轮换机器狗的 SSH/sudo 密码；把 `dogssh.sh`、`dogsudo.sh`、`rsudo.sh`、`env.sh` 改为读取环境变量；用 `git filter-repo` 清除历史中的密码（仓库是公开的）。
2. 修正 `DEVELOPER_GUIDE.md` §4.1 的映射对调、§4.5 的 kp/kd 表；重新生成或删除 `runner_params.json` 的 kp/kd 字段；把 `sim2sim_deployed.py:31` 改为 0.01，并给 runner 补上 0.05/0.0333 覆写后重跑回归。
3. 把 STATUS、DG §7.1、`mapping_sim_report.md` 里的 "281 m / 6.46 m/s" 改为"疑似 /ODOM 异常，未证实"。
4. 统一 EtherCAT→CAN-FD、FIFO→RR、decimation 4→20（部署版）、`kRLControl=17`；在 06 开头标注"SDK 版"。
5. 把本文 §3.3 的 drdds 重建方式和 SDK x86 编译补进仓库（建议提交 `drdds` 的 `CMakeLists.txt`）。
6. 从仓库移除 `sim/ws/build`、`sim/ws/install`、`sim/nav_sim/nav_closed_loop` 二进制。
7. 把 `.dpkg/info` 打包成 tar，或从仓库移除，以便 Windows 用户能正常检出。
