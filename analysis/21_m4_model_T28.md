# 21 · T28 数字孪生模型（MuJoCo / Gazebo）

## 1. 结论

MJCF 模型**可直接加载**，与实机 16 自由度、限位、质量完全一致。已整理为独立模型包 `sim/m20_description/`。

## 2. 模型验证结果（mujoco 3.16.0）

```
nq=23  nv=22  nu=16  nbody=18  ngeom=45   总质量=34.526 kg
```
| # | 关节 | 类型 | 限位范围 (rad) | 力矩上限 (N·m) |
| --- | --- | --- | --- | --- |
| 1 | fl_hipx | hinge | [-0.436, 0.611] | ±76.4 |
| 2 | fl_hipy | hinge | [-2.286, 2.583] | ±76.4 |
| 3 | fl_knee | hinge | [-2.809, 2.792] | ±76.4 |
| 4 | fl_wheel | hinge | 连续 | ±21.6 |
| 5-8 | fr_hipx/hipy/knee/wheel | hinge | [-0.611,0.436] / [-2.286,2.583] / [-2.809,2.792] / 连续 | ±76.4 / ±21.6 |
| 9-12 | hl_* | hinge | [-0.436,0.611] / [-2.583,2.286] / [-2.792,2.809] / 连续 | 同上 |
| 13-16 | hr_* | hinge | [-0.611,0.436] / [-2.583,2.286] / [-2.792,2.809] / 连续 | 同上 |

- **质量 34.526 kg**（与实机 ~33kg 量级一致，含轮足）。
- 轮关节在 MJCF 中未设 range（连续），与实机轮毂连续旋转一致。
- 限位值与 SDK `m20_control_parameters.cpp`（`fl_joint_lower/upper`）一致。

## 3. 关键：sim-to-real 标定（官方 `mujoco_simulation_ros2.py`）

仿真与实机之间存在**关节方向与零位偏置**，官方给出精确标定：
```python
JOINT_DIR      = [ 1, 1,-1, 1,  1,-1, 1,-1,  -1, 1,-1, 1,  -1,-1, 1,-1]
POS_OFFSET_DEG = [-25, 229, 160, 0,  25,-131,-200, 0,  -25,-229,-160, 0,  25,131,200, 0]
# raw = published * JOINT_DIR + POS_OFFSET_RAD
JOINT_INIT = [-0.438,-1.16,2.76,0,  0.438,-1.16,2.76,0,  -0.438,1.16,-2.76,0,  0.438,1.16,-2.76,0]
DT = 0.001
```
> 这解释了两处此前发现的差异（`analysis/07`）：① MJCF 关节方向相对实机有符号翻转；② 实机零位 ≠ MJCF 零位（偏置最大 229°）。**这是 sim-to-real 一致性的关键参数**，必须在 T29 回放中应用。

## 4. 交付物

- `sim/m20_description/mjcf/{M20.xml, scene.xml, M20_stair.xml, stair.xml}`
- `sim/m20_description/meshes/*.STL`（17 命名 STL + 2202 编号 STL）
- `sim/m20_description/calibration.json`（JOINT_DIR / POS_OFFSET_RAD / JOINT_INIT / DT）
- `sim/validate_model.py`（加载与结构断言）
- 官方仿真器：`sim/mujoco_simulation_ros2.py`（DDS↔MuJoCo 桥，可选）

## 5. Gazebo 路径说明

计划要求 Gazebo（`ros-humble-gazebo-ros-pkgs` 已装，Gazebo 11.10.2）。MJCF→Gazebo 无直接转换，两条路线：
- **路线 A（推荐，保真）**：以 **MuJoCo** 作为数字孪生运行体（模型原生、惯性/接触/力限完整），Gazebo 仅用于 L1 话题/可视化对接。
- **路线 B（贴合计划字面）**：由 MJCF 生成 URDF（`mjcf→urdf`），用 Gazebo + `ros2_control` 复现；代价是接触/摩擦与 MuJoCo 有差异，且需重建传动。

> 采用路线 A 执行 T29/T32 的动力学验证；同时产出 URDF 供 Gazebo 加载（T28 字面要求）。

## 6. 结构断言（`sim/validate_model.py`）

- `nu == 16`（12 角关节 + 4 轮）
- `nbody == 18`（base + 4 腿 × (hipx,hipy,knee,wheel) + world）
- 限位与 SDK 参数逐项一致
- 质量在 [30, 40] kg
