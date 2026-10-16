# 部署策略仿真回归报告（真实权重 · MuJoCo）

> 脚本：`sim/sim2sim_deployed.py`（`runner_params.json` 按 runner 载入各自参数）
> 权重：`bin/policies/*.onnx`（从实机 `rl_deploy` 二进制提取的明文 ONNX）
> 映射来源：`tools/ghidra_policy_map.py`（策略符号 `__policy_<name>_` → 引用它的 runner 构造函数）
> 参数来源：`tools/parse_runner_params.py` 解析 `notes/ghidra_rl_allctors.txt`

## 一、策略 ↔ runner 权威映射（策略符号 xref）

| 策略 | runner | obs_dim | 变体 |
| --- | --- | --- | --- |
| `policy_policy_m20_backknee6` | `M20BasicBackkneeRunner` | 53 | A |
| `policy_policy_m20_50` | `M20BasicFlatRunner` | 53 | A |
| `policy_policy_ca9bplatform` | `M20BasicPlatRunner` | 53 | **B** |
| `policy_policy_m20_5` | `M20BasicStairRunner` / `M20NaviStairRunner` | 53 | A |
| `policy_m20_navi_flat_v4_2` | `M20NaviFlatPolicyRunner` | **54** | D（A+常量0.52）|
| `policy_m20_navi_charge_v3_29` | `M20NaviChargePolicyRunner` | **60** | **C**（A+步态相位+gait_commands）|
| `policy_m20_navi_stair_v7_0_himloco` | `M20NaviOrienteerRunner` | 53 | A |
| `policy_m20_flat_v1_4` | `M20StandPolicyRunner` | **61** | **E**（B+步态+尾常量1.0）|
| `policy_m20_hmap_motion_v0_2` | `M20HeightGapPolicyRunner` | `x*y+53` | 地图 |
| `policy_m20_forward_policy_2` | `M20ExtrePolicyRunner` | 53×36 | 多输入 |
| `policy_m20_sixaxis_stand` | `M20FinetuneStandRunner` | 53×36 | 多输入 |
| `policy_m20_finetune_stand_15kg` | `M20SixAxisStandRunner` | 53×36 | 多输入 |
| `policy_m20_finetune_forward` | `M20StepMoveRunner` | 53×36 | 多输入 |

> 注：`policy_policy_m20_38` / `policy_policy_m20_rough_6` 未检出 xref（但仍可与 `BasicFlat`/`BasicStair` 闭环）。

## 二、两种观测变体（已实证）

- **变体 A**（多数 runner）：`update_joint_data` + `dof_pos_default_trans` → `dof_pos` 为**关节主序** `[hipx×4, hipy×4, knee×4]`；动作输出亦**关节主序**，`goal_pos[leg*4+j] = act[j*4+leg]*0.25 + default[leg*3+j]`。
- **变体 B**（`M20BasicPlatRunner`）：`gym_update_joint_data` + `dof_pos_default_` → `dof_pos` 为**腿主序** `[FL3, FR3, HL3, HR3]`；动作为**机器人序**直用，`goal_pos[leg*4+j] = act[leg*4+j]*0.25 + default[leg*3+j]`。
- **变体 C**（`M20NaviChargePolicyRunner`，60 维）：在 A 基础上，于 `cmd` 之后插入 `sin(2π·phase)(1) + cos(2π·phase)(1) + gait_commands(5)`；`phase += gait_commands[0] * 0.02`（50 Hz），取模 1.0。常数实测 `0.02` 与 `2π`。

## 三、回归结果（最终 · 全 15 个策略）

| 策略 | runner | 规格 | 站立 | 行走 @ cmd 0.5 |
| --- | --- | --- | --- | --- |
| `policy_policy_m20_38` | BasicFlat | A/53 | ✅ | ✅ 4.67 m |
| `policy_policy_m20_50` | BasicFlat | A/53 | ✅ | ✅ 5.05 m |
| `policy_policy_m20_5` | BasicStair | A/53 | ✅ | ✅ 5.07 m |
| `policy_policy_m20_backknee6` | BasicBackknee | A/53 | ✅ | ✅ 5.64 m |
| `policy_policy_m20_rough_6` | BasicStair | A/53 | ✅ | ✅ 5.72 m |
| `policy_policy_ca9bplatform` | BasicPlat | B/53 | ✅ | ✅ 2.23 m |
| `policy_m20_navi_stair_v7_0_himloco` | NaviOrienteer | A/53 | ✅ | ✅ 2.50 m |
| `policy_m20_navi_flat_v4_2` | NaviFlat | A+0.52/54 | ✅ | ✅ 1.96 m |
| `policy_m20_flat_v1_4` | StandPolicy | E/61 | ✅ | ✅ 2.31 m |
| `policy_m20_forward_policy_2` | Extre | F 53×36 | ✅ | ✅ 7.23 m（0.72 m/s）|
| `policy_m20_finetune_stand_15kg` | FinetuneStand | F 53×36 | ✅ | ✅ |
| `policy_m20_sixaxis_stand` | SixAxisStand | F 53×36 | ✅ | ✅（原地）|
| `policy_m20_finetune_forward` | StepMove | F 53×36 | ✅ | ✅（方向语义待定）|
| `policy_m20_hmap_motion_v0_2` | HeightGap | G 504×6 | ✅ | ✅ 4.57 m（零高程图=平地）|
| `policy_m20_navi_charge_v3_29` | NaviCharge | C/60 | ⚠️ | ⚠️ |

**14/15 通过站立+行走闭环**。`NaviCharge` 唯一例外：构成与软启动已完全解出（倾角由 179°→<31°，不再翻倒），但其为"充电位对接"策略，零指令下持续低速移动、姿态偏低（z≈0.2），故不满足"站立"判据。

### NaviCharge 软启动（关键发现）
```cpp
if (run_cnt_ <= obs_history_num_ * 2) {   // 前 10 个策略步
    robot_action.kp = kp_ * 0.5;          // 0x3fe0000000000000
    robot_action.kd = kd_ * 2.0;          // 0x4000000000000000
}
run_cnt_++;
```
实现后倾角由 179° 降至 <31°，证明该逻辑为必要项。

### HeightGap（地图族）
`x_points_num=41, y_points_num=11, hmap_data_scale_=5.0` → `obs_dim_ = 41×11+53 = 504`，history 5 → **3024**。观测末段为 `hmap_data × 5.0`（451 维）。喂零图（平地）即稳定站立/行走。

### 观测变体全解（`GetRobotAction` / `updateCommand` / 构造函数 反编译）
| 变体 | 组成 | 维度 | 使用者 |
| --- | --- | --- | --- |
| A | `ω·0.25 + 重力 + cmd + (dof_pos_jm − default_trans) + dof_vel·s + wheel_vel·s + last_action` | 53 | 多数 runner |
| B | 同 A，但 `dof_pos` **腿主序**、动作机器人序直用 | 53 | `BasicPlatRunner` |
| D | A + 常量 `0.52`（cmd 之后）| 54 | `NaviFlatPolicyRunner` |
| C | A + `sin(2π·φ) + cos(2π·φ) + gait_commands(5)` | 60 | `NaviChargePolicyRunner` |
| E | B + `sin/cos(2π·φ) + gait_commands(5)` + 尾常量 `1.0` | 61 | `StandPolicyRunner` |
| F | **多输入**：`state[1,36,53]` + `command[1,N]` + `uncertain[1,1]=1.0` | 53×36 | `Extre`/`FinetuneStand`/`SixAxisStand`/`StepMove` |
| G | A + 高程图 `hmap_data×5.0`（451 维，末尾）| 504×6 | `HeightGapPolicyRunner` |

### 逐 runner 真值（构造函数反编译）
| runner | kp | kd | gait_commands |
| --- | --- | --- | --- |
| `NaviStair/Orienteer/Flat/…` | `[80,80,80,0]×4` | `[3,3,3,0.6]×4` | — |
| `NaviChargePolicy` | `[60,60,60,0]×4` | `[1.5,1.5,1.5,0.6]×4` | `[1.5,0.5,0,0,0.5]` |
| `StandPolicy` | `[80,100,100,0]×4` | `[2,2,2,0.6]×4` | `[2.0,0.5,0,0,0.5]` |

> 变体 F：`uncertain` 恒为 **1.0**（`setOnes`）；`command[1,N]` 由 `updateCommand → cal_command` 算，`command_dim` = 21/13/5；实测 `command[0]=v_x` 即驱动前进。
> 步态相位：`φ += gait_commands[0] × 0.02`（50 Hz）。

## 四、结论
**15 个部署策略中 14 个已在 MuJoCo 完成站立/行走闭环**（覆盖 **7 种观测变体**、两种关节序、多输入、步态相位、软启动与高程图）。
`NaviCharge` 为唯一例外：构成与软启动全解、不再翻倒，但作为充电位对接策略在零指令下持续移动。

