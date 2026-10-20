# M20 在 WSL 中的 Gazebo / MuJoCo 仿真部署与算法测试指南

> 适用：Windows 11 + WSL2 Ubuntu 22.04 + ROS 2 Humble（本机已具备 Gazebo Classic 11、MuJoCo 3.16、RTX 4060 + WSLg）
> 所有命令均已在本机实测，结果数字来自 2026-10-16 的实际运行。
> 源码：`E:\ccmax\rev_robot\m20_sim\`（在 WSL 中为 `/mnt/e/ccmax/rev_robot/m20_sim`）；构建产物：WSL 中 `~/m20_sim_ws`

---

## 0. 结论先看

| 仿真方式 | 用途 | 状态 |
| --- | --- | --- |
| **A. Gazebo + 官方 rl_deploy（ROS 全链路）** | 完整 ROS 栈测试、导航/感知联调、接近实机的话题接口 | ✅ **推荐**。站立 → RL → 行走 2.7 m/5 s → 转向，倾角 < 1° |
| **B. MuJoCo 进程内（Python）** | 运控算法开发、批量测试、调参，速度约实时的 20 倍 | ✅ **推荐**。站立、行走 5.2 m/10 s、转向、爬楼梯均通过 |
| C. MuJoCo + 官方 rl_deploy（ROS 全链路） | 与 A 相同接口 | ⚠️ **已知问题**：进入 RL 约 2 s 后倾倒。**官方 SDK 原版同样复现**，并非本方案引入。详见 §6 |

**两条仿真链路共用一套接口**：`/JOINTS_CMD`、`/JOINTS_DATA`、`/IMU_DATA`（drdds 消息，200 Hz），与实机话题名和类型一致。你的算法节点写一次，即可在 Gazebo、MuJoCo 和实机之间切换。

---

## 1. 一次性环境搭建

```bash
# WSL 终端中执行（约 3 分钟）
bash /mnt/e/ccmax/rev_robot/m20_wsl_scripts/00_setup_python_venv.sh      # 若已建过 ~/.venvs/m20 可跳过
tr -d '\r' < /mnt/e/ccmax/rev_robot/m20_sim/setup_m20_sim.sh > /tmp/setup_m20_sim.sh
REPO=/mnt/e/ccmax/rev_robot SIM_SRC=/mnt/e/ccmax/rev_robot/m20_sim W=~/m20_sim_ws bash /tmp/setup_m20_sim.sh
```

构建出三个包：

| 包 | 内容 |
| --- | --- |
| `drdds` | 用 dump 中的 60 msg + 8 srv 在 Humble 下重建的厂商消息包 |
| `m20_sdk_deploy` | 官方 SDK（x86），**打了一个补丁**：新增 ROS 话题指令源（见 §2.3） |
| `m20_gazebo` | 从官方 MJCF 生成的完整 URDF、Gazebo drdds 桥插件、world、launch、工具脚本 |

之后每个新终端先执行：

```bash
source ~/m20_sim_ws/env.sh
```

只改了 `m20_gazebo` 源码时，用 `bash /mnt/e/ccmax/rev_robot/m20_sim/rebuild_gazebo_pkg.sh` 快速重编（需先 `tr -d '\r'` 转换换行符，或在 WSL 中保存）。

---

## 2. 方式 A：Gazebo 全链路（推荐）

### 2.1 启动

```bash
source ~/m20_sim_ws/env.sh
# 带图形界面（WSLg），同时启动官方控制器
ros2 launch m20_gazebo m20_gazebo.launch.py rl_deploy:=true
# 无界面（服务器 / 批量测试）
ros2 launch m20_gazebo m20_gazebo.launch.py gui:=false rl_deploy:=true
```

启动顺序由 launch 文件处理：先启动 Gazebo，再生成机器人，**之后才启动 `rl_deploy`**。原因是 `rl_deploy` 启动时会阻塞，直到收到全部 16 个关节的数据。

launch 参数：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `gui` | `true` | 是否打开 Gazebo 窗口 |
| `rl_deploy` | `false` | 是否同时启动官方控制器（测自己的控制器时设 false） |
| `world` | `m20_flat.world` | 平地 + x=4 m 处三级台阶（8/16/24 cm） |
| `z` | `0.2` | 生成高度 |

### 2.2 控制机器人（另开终端）

```bash
source ~/m20_sim_ws/env.sh
ros2 run m20_gazebo m20_cmd.py stand              # 站立（需等约 4 s 完成）
ros2 run m20_gazebo m20_cmd.py rl                 # 切换到 RL 控制
ros2 run m20_gazebo m20_cmd.py vel 0.6 0 0 5      # 前进，参数：前向 侧向 偏航 ∈[-1,1]，持续秒数
ros2 run m20_gazebo m20_cmd.py vel 0 0 0.6 3      # 原地左转
ros2 run m20_gazebo m20_cmd.py damp               # 泄力（关节阻尼）
ros2 run m20_gazebo m20_cmd.py status             # 打印 IMU 姿态与关节角
ros2 run m20_gazebo base_pose.py watch 10         # 真值位姿（Gazebo 内部状态），每秒一行
```

状态机约束与实机一致：只能按 `idle → stand → rl` 的顺序切换，`damp` 任何时候都可以。越级指令会被拒绝，并打印 `[RosCmd] mode … rejected`。

### 2.3 指令接口（给你的算法用）

打补丁后的 `rl_deploy` 默认从 ROS 话题读取指令（环境变量 `M20_CMD_SOURCE=ros`；也可设为 `keyboard` 或 `gamepad`）：

| 话题 | 类型 | 含义 |
| --- | --- | --- |
| `/sim_cmd` | `geometry_msgs/Twist` | `linear.x`、`linear.y`、`angular.z` 分别为前向、侧向、偏航速度比例 ∈[-1,1]。**0.5 s 未收到新指令则自动归零**（死人开关） |
| `/sim_mode` | `std_msgs/UInt8` | 1 = 站立，6 = RL，2 = 阻尼 |

**接入导航算法**：把你的规划器输出发到 `/sim_cmd`，按 20 Hz 以上持续发布即可。

### 2.4 实测结果（本机，无界面）

| 指标 | 结果 |
| --- | --- |
| `/JOINTS_DATA`、`/JOINTS_CMD` 频率 | 199.8 / 200.0 Hz |
| 实时率（RTF） | 1.00 |
| 站立高度 | 0.10 m（趴）→ 0.45 m |
| 前进 5 s（指令 0.6） | 2.74 m，倾角 0.9° |
| 原地转 4 s（指令 0.6） | 偏航约 70°，倾角 1.0° |
| IMU `acc_z`（静止） | 9.81–9.88 m/s² |

一键复现：`bash /mnt/e/ccmax/rev_robot/m20_sim/tests/test_gazebo_headless.sh`

---

## 3. 方式 B：MuJoCo 进程内（推荐用于运控算法）

```bash
PY=~/.venvs/m20/bin/python
S=/mnt/e/ccmax/rev_robot/m20_sim/mujoco/mujoco_inproc.py
MJ=/mnt/e/ccmax/rev_robot/sim/m20_description/mjcf
P=/mnt/e/ccmax/rev_robot/dump/hostA/home_user/sdk_deploy/src/M20_sdk_deploy/policy/policy.onnx

$PY $S --policy $P --mjcf-dir $MJ --vx 0.6 --secs 10                   # 平地行走
$PY $S --policy $P --mjcf-dir $MJ --vx 0.6 --secs 10 --scene stair     # 楼梯场景
$PY $S --policy $P --mjcf-dir $MJ --vx 0.6 --secs 20 --viewer          # 实时可视化（WSLg）
$PY $S --policy $P --mjcf-dir $MJ --vx 0.6 --csv /tmp/traj.csv         # 导出轨迹 t,x,y,z,tilt
```

实测（10 s 仿真，50 Hz 策略，即 SDK 实际频率）：

| 场景 | 结果 | 墙钟时间 |
| --- | --- | --- |
| 原地站立 | HELD，倾角 0.7° | 0.4 s |
| 前进 vx=0.6 | HELD，5.18 m，倾角 3.5° | 0.4 s |
| 原地转 wz=0.6 | HELD，倾角 2.5° | 0.4 s |
| 楼梯 vx=0.6 | HELD，登上 1.1 m 台阶顶部，倾角 19° | 1.5 s |

**接入你自己的控制器**：照 `SdkPolicy` 写一个类，`__call__(state, cmd)` 返回 `goal_pos, goal_vel, kp, kd`（机器人序 16 维，MJCF 角度域），再把 `controller = SdkPolicy(...)` 换成你的类。

- `state` 含 `q`、`dq`、`quat`(wxyz)、`acc`、`gyro`、`base_pos`（真值）。
- 力矩按 `kp·(goal_pos−q) + kd·(goal_vel−dq)` 计算，并截断在 ±76.4 / ±21.6 N·m。
- 跑 15 个**部署策略**（53×6 观测）请用仓库的 `sim/sim2sim_deployed.py`，注意先按技术文档 §2.1 修正 `WHEEL_VEL_SCALE` 和 kp/kd。

---

## 4. 写自己的 ROS 算法节点（两种仿真通用）

| 你要做的 | 订阅 | 发布 | `rl_deploy` |
| --- | --- | --- | --- |
| 导航 / 高层规划 | `/IMU_DATA`、真值（Gazebo `/gazebo/get_entity_state`） | `/sim_cmd` | 开启 |
| 自研底层控制器（替换 RL） | `/JOINTS_DATA`、`/IMU_DATA` | `/JOINTS_CMD` | **关闭**（`rl_deploy:=false`） |

自研底层控制器要注意：

1. `/JOINTS_CMD` 和 `/JOINTS_DATA` 里的角度是**实机编码器域**：`raw(MJCF) = pub × dir + offset`。`dir` 和 `offset` 见 `m20_gazebo_bridge.cpp` 中的 `kJointDir` / `kPosOffsetDeg`，与官方 MuJoCo 桥完全一致。
2. 仿真里的力矩律是 `τ = kp·(pos−q) + kd·(vel−dq) + torque`，在每个物理步（1 kHz）计算并按关节上限截断。
3. 至少以 200 Hz 发送 `/JOINTS_CMD`。
4. 消息结构参考 `~/m20_sim_ws/src/drdds/msg/JointsDataCmd.msg`；Python 里 `from drdds.msg import JointsDataCmd`。

C++ 节点在 `package.xml` 和 CMake 中依赖 `drdds` 即可。

---

## 5. 文件说明

```
E:\ccmax\rev_robot\m20_sim\
├── setup_m20_sim.sh            # 一键构建 drdds + SDK(补丁) + m20_gazebo，生成 env.sh
├── rebuild_gazebo_pkg.sh       # 只重编 m20_gazebo
├── sdk_patch/
│   ├── ros_cmd_interface.hpp   # 新增指令源：/sim_cmd + /sim_mode
│   └── apply_sdk_patch.py      # 打补丁（幂等，只增不删，环境变量选择指令源）
├── m20_gazebo/
│   ├── scripts/mjcf_to_gazebo_urdf.py  # MJCF → URDF（网格外观、27 个碰撞体、完整惯量张量、连续轮关节）
│   ├── src/m20_gazebo_bridge.cpp       # Gazebo 插件：drdds 桥，与官方 MuJoCo 桥行为一致
│   ├── worlds/m20_flat.world           # 1 kHz ODE、平地 + 台阶、真值状态服务
│   ├── launch/m20_gazebo.launch.py
│   └── scripts/{m20_cmd.py, base_pose.py, record_joints.py, run_mujoco_bridge.py}
├── mujoco/mujoco_inproc.py     # 方式 B
└── tests/{test_gazebo_headless.sh, test_mujoco_headless.sh, ab_mujoco.sh}
```

生成的 URDF 位于 `~/m20_sim_ws/install/m20_gazebo/share/m20_gazebo/urdf/m20.urdf`：

- 已核验：总质量 34.526 kg，12 个转动关节 + 4 个连续轮关节，惯量全部正定，`gz sdf` 转换无误。
- 也可用作 Isaac Sim URDF Importer 的输入。

---

## 6. 已知问题与限制

1. **MuJoCo + 跨进程 rl_deploy 会倾倒（方式 C）**
   - 进入 RL 约 2 s 后倾角发散，随后轮速失控。
   - 官方 SDK 原版的 `mujoco_simulation_ros2.py` 同样复现（A/B 测试：`tests/ab_mujoco.sh`）。
   - 已排除的原因：
     - 物理模型：同一模型在进程内同步运行时稳定；
     - 通信延迟：注入 10 ms 观测延迟和 10 ms 动作延迟仍稳定；
     - 仿真步进：已改为追赶式步进，RTF 稳定在 1.00；
     - 关节零偏：两侧仿真的偏置修正完全相同；
     - 场景：出生点附近无障碍物；
     - IMU 一致性：姿态角变化率与陀螺仪读数相关性正常。
   - 根因尚未定位，可能与官方桥的初始化姿态和站立交接过程有关。
   - **结论**：需要 ROS 全链路时用 Gazebo；在 MuJoCo 中测运控算法时用方式 B。
2. **Gazebo 与 MuJoCo 的物理差异**
   - Gazebo（ODE）的接触比 MuJoCo 软，轮地摩擦也是近似值，行走距离会有约 10% 差异。
   - 做 sim2sim 验证时，两边各跑一遍再比较。
3. **SDK 策略不是实机部署策略**
   - 官方 SDK 用的是 57 维观测的 `policy.onnx`。
   - 实机 `rl_deploy` 内嵌的是另外 15 个策略（53×6 观测），在 ROS 链路中跑它们需要另写 runner。目前可以用仓库的 `sim2sim_deployed.py` 在 MuJoCo 中进程内运行。
4. **Gazebo 中的 IMU 加速度**由速度差分得到（Gazebo Classic 的加速度接口不含接触力），含轻度低通，静止时为 9.81。
5. **没有激光雷达仿真**。需要做 SLAM 联调时，可在 URDF 中加 `gazebo_ros_ray_sensor`（实机为双 Robosense Airy，前后各一，安装位置 x=±0.32 m），话题名设为 `/LIDAR/POINTS`。
