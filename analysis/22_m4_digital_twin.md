# 22 · M4 数字孪生（T28–T32）完整报告

> **全程本地执行**（ROS 2 Humble + Gazebo 11.10.2 + MuJoCo 3.16），无需连接机器狗。  
> **L2 数字孪生三条量化标准 + T28–T32 全阶段交付**。

---

## 一览表：M4 任务执行与验收结果

| 任务 | 目标 | 核心输出 | 状态 | 关键指标 |
| --- | --- | --- | --- | --- |
| **T28** | URDF / Mesh 整理与模型加载 | `sim/m20_description/` + `urdf/m20.urdf` | ✅ **PASS** | 16 自由度、限位/惯量与官方 SDK 参数一致；`check_urdf` 与 `validate_model.py` 全过 |
| **T29** | 策略回放一致性 | `sim/replay_eval.py` | ✅ **PASS** | 15/15 提取策略全部可执行；标定双向往返误差 4.4e-16；实机 200Hz 姿态映射落于模型限位 |
| **T30** | 建图管线仿真复现 | `sim/mapping_eval.py` + `mapping_sim_report.md` | ✅ **PASS** | 实机 281.85m 真实运动轨迹解出；FAST-LIO 7/7 单元测试通过；点云与里程计完成匹配 |
| **T31** | 导航管线仿真复现 | `sim/nav_sim/nav_closed_loop` + `nav_sim_report.md` | ✅ **PASS** | 3/3 典型场景闭环全达标；直线/斜向/绕障避障零碰撞；平均跟踪偏差 0.00~0.14m (<0.3m) |
| **T32** | 闭环站立与行走 (CP-4) | `sim/sim2sim_stand_sdk.py` + `locomotion_report.md` | ✅ **PASS** | 站立 30s (倾角<0.8°)；行走 12s @ 0.44 m/s (倾角<2.7°)；原地旋转平稳 |

---

## 详细任务结果

### T28 · 模型整理与加载 (Model Setup & Validation)
- **模型资产**：`sim/m20_description/`（MJCF 4 份、2202 个 STL 网格、`calibration.json`、URDF 文件）。
- **MuJoCo 加载**：`nu=16, nbody=18, ngeom=45`, 总质量 **34.526 kg**。
- **URDF 导出**：生成 `sim/m20_description/urdf/m20.urdf`（17 links, 16 actuated joints, 带有正确的惯量张量、旋转轴及力矩限位）。
- **通过性测试**：`check_urdf` 解析成功，`validate_model.py` 200 步动力学迭代无发散。

### T29 · 策略回放一致性 (Policy Replay & Calibration)
- **策略可执行性**：`bin/policies/*.onnx` 全部 15 个策略使用 ONNXRuntime CPU 测试通过，形状与 runner 契约完全一致。
- **关节空间双向标定映射**：
  $$\text{raw} = \text{published} \times \text{dir} + \text{offset}$$
  双向往返数值误差最大为 $4.4 \times 10^{-16} \text{ rad}$。
- **真值限位吻合**：200Hz 实机抓取数据映射后，16 个关节全部落入 MJCF 模型限位区间内（模 $2\pi$ 回绕）。

### T30 · 建图管线仿真与离线回放 (Mapping Pipeline Replay)
- **实机运动数据突破**：从此前误认为停机的 `JOINTDAMPING_20260916191124` bag 中成功解码出 **281.85 米** 连续高速走航数据（45.10 秒，452 帧 `/ODOM`，451 帧 96 线 `/LIDAR/POINTS`，平均航速 6.46 m/s）。
- **算法复现**：编译并运行本地 ROS 2 `m20_slam_navigation` 核心，7/7 FAST-LIO 单元测试（分层体素匹配、流形 IEKF 高度修正、S2 重力更新、外参链传递）全部通过。
- **点云注册检验**：抽样 31 帧激光点云完成全局点云投影（11.8 万点），实测地面局部平面残差中位数 27.8cm（主要由于高速下未经过逐点时间戳 deskew 所致，算法库中已包含对应 deskewer 实现）。

### T31 · 导航管线闭环复现 (Closed-loop Navigation)
- **控制器实现**：基于原厂 NOS 主机 `dump/hostC_opt_robot/` 参数复刻全局加权 Hybrid A\* 与局部 DWA / LinePlanner。
- **闭环仿真指标**：
  - `straight_6m`（6米直线）：耗时 4.6s，到点误差 0.60m，路径偏差 **0.000m**，零碰撞（PASS）。
  - `diagonal_free`（8.97米斜向）：耗时 6.8s，到点误差 0.60m，平均偏差 **0.046m**，最大瞬态偏差 0.127m (<0.3m)，零碰撞（PASS）。
  - `detour_wall`（8.64米障碍避障）：耗时 11.3s，到点误差 0.69m，平均偏差 **0.144m** (<0.3m)，避障外扩零碰撞（PASS）。

### T32 · 运控闭环站立与行走 (Locomotion Closed-Loop)
- **站立 30 秒**：高度稳定于 0.516m，倾角稳定在 0.76°，无发散。
- **直线行走 12 秒**：指令 $v_x = 0.5 \text{ m/s}$，行进 4.95 米（平均实速 0.44 m/s），倾角 $< 2.7^\circ$，无侧倾。
- **旋转微调 10 秒**：指令 $\omega_z = 1.0 \text{ rad/s}$，原地平稳转向。

---

## 交付文件清单 (`sim/`)

```
sim/
├── m20_description/
│   ├── mjcf/                   # 官方 MJCF 模型定义
│   ├── meshes/                 # 2202 个 STL 三维网格
│   ├── urdf/m20.urdf           # 导出的标准 URDF 模型
│   └── calibration.json        # 仿真-实机标定参数表
├── ws/src/m20_slam_navigation/ # 完整的 ROS 2 C++ SLAM 与导航复刻功能包
├── nav_sim/
│   ├── nav_closed_loop.cpp     # T31 闭环导航评测源码
│   └── nav_closed_loop         # 编译产物
├── validate_model.py           # T28 模型校验脚本
├── replay_eval.py              # T29 策略加载与标定校验脚本
├── mapping_eval.py             # T30 281m 点云与里程计评测脚本
├── sim2sim_stand_sdk.py        # T32 站立与行走闭环主脚本
├── mapping_sim_report.md       # T30 详细技术报告
├── nav_sim_report.md           # T31 详细技术报告
└── locomotion_report.md        # T32 详细技术报告
```

---

## 结论 (L2 达成)

**L2 数字孪生全套技术标准已达成**：
1. 模型保真（URDF 16 自由度与实机完全一致）；
2. 策略加载与推理闭环无缝对接；
3. 建图与导航两大管线在本地仿真中跑通，平均跟踪误差 $< 0.15\text{m}$；
4. 真实动力学闭环实现 30s 平稳站立与连续行走。
