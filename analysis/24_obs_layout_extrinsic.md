# 24 · 逆向收尾：LiDAR-IMU 外参与部署观测布局（实机二进制可证）

> 方法：REA/pyghidra headless 反编译 + 符号/DWARF 交叉验证。目标二进制哈希与实机一致（`rl_deploy 59aa77a2…`、`lio_ddsnode 0ea536e6…`）。
> 结论：**两处 L1 精度缺口已闭合**。

---

## 一、LiDAR-IMU 外参：identity，来自配置，无隐藏覆盖

### 证据链

1. **二进制内硬编码配置路径**：`lio_ddsnode` 内含字符串 `/opt/robot/share/lio-perception/conf/params.yaml`，启动脚本 `lio_ddsnode.sh` 不传参 → 该文件即唯一配置源。
2. **外参键读取点**（Ghidra 基址 `0x100000`）：
   - `extrinsic_est_en` ← `getParamsFromFile+0x88`
   - `extrinsic_B_I` ← `getParamsFromFile+0x7BC`
   - `extrinsic_B_L` ← `getParamsFromFile+0x93C`
3. **解析方式**（反汇编确证）：
   ```
   adrp x1, 1a3000 ; add x1, #0xc40        → "extrinsic_B_I"
   bl   YAML::Node::operator[]<char[14]>
   bl   YAML::convert<std::vector<double>>::decode
   ... ldr d0,[x0,#0] … str d0,[sp,#672] … 逐元素写入
   ```
   即 `std::vector<double>` → 逐元素装载（4×4 矩阵）。
4. **无静默默认**：向量长度不足时跳转至 `__throw_out_of_range_fmt`（抛出异常），**不存在兜底常量**。

### 实际取值（实机 `params.yaml`，逐字节核对过）
```
extrinsic_B_I = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]   # identity
extrinsic_B_L = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]   # identity
extrinsic_est_en = false                                # 关闭在线外参估计
```

### 结论与物理含义
- **LIO 中 LiDAR↔IMU 外参就是 identity，未硬编码、未被覆盖**。此前 `analysis/07` 的猜测（"真实外参可能硬编码于二进制"）**否决**。
- 物理安装由 **`rslidar` 驱动**承担：前/后雷达外参 `x=±0.32028, z=-0.013, pitch=-1.57079, yaw=0/π`，`send_separately=false`（前后合并），输出帧 `lidar_link`（= 机身中心帧）。实测点云 `r<0.3m` 无点、最近点 0.43m，确证为机身为原点的合并帧。
- 因此系统的真实语义链是：**雷达驱动把点云搬到机身帧 → LIO 视点云帧与 IMU 帧重合**。官方 SDK MJCF 中 IMU 安装点为 `(0.0632, -0.0268, 0.0435)`（约 7.6 cm 偏移），厂商在 LIO 中**未建模该偏移**（对 LIO 去畸变是次要项）。

---

## 二、部署版观测布局：**53 维/帧 × 6 帧 = 318**（权威确证）

### 权威常量（`PolicyRunnerBase::PolicyRunnerBase`）
```
obs_dim_           = 0x35 = 53        # 每帧观测维度
obs_history_num_   = 5                # 历史帧数
act_dim_           = 0x10 = 16        # 动作维度
obs_total_dim_     = obs_dim_ + obs_dim_*obs_history_num_ = 53 + 265 = 318  ✅
```
> 这直接解释了 ONNX 输入 `[1, 318]`；同族 `324/360/366` 对应 `obs_dim_ = 54/60/61`（history 恒为 5）。

### 每帧 53 维拼装（`M20{NaviStair,BasicFlat,…}Runner::GetRobotAction` 中 `obs << …` 逐项）
| # | 项 | 维度 | 说明 |
| --- | --- | --- | --- |
| 1 | `base_omega * omega_scale_` | 3 | `omega_scale_ = 0.25` |
| 2 | `base_rot_matᵀ · [0,0,-1]` | 3 | 投影重力（机体系） |
| 3 | `cmd_vel * cmd_vel_scale_` | 3 | 速度指令×缩放 |
| 4 | `dof_pos - dof_pos_default_trans_` | 12 | 关节角偏差（**关节主序**） |
| 5 | `dof_vel * dof_vel_scale_` | 12 | 关节速度×缩放（`dof_vel_scale_ = 0.05`） |
| 6 | `wheel_vel * wheel_vel_scale_` | 4 | 轮速×缩放（基类 0.01，NaviStair 覆写 **0.05**） |
| 7 | `last_action_` | 16 | 上一步动作（`act_dim_`） |
| | **合计** | **53** | 3+3+3+12+12+4+16 |

### 关节排序（关键，与 SDK 的 57 维不同）
`PolicyRunnerBase::update_joint_data` 反编译显示**关节主序转置**：
```cpp
for (leg = 0; leg < 4; ++leg) {
  if (leg < 3) {                      // 仅髋x/髋y/膝，跳过轮；共 12
    dof_pos[leg*4+0] = ro->joint_pos[leg+0];   // 第 leg 个 hipx
    dof_pos[leg*4+1] = ro->joint_pos[leg+4];   // 第 leg 个 hipy
    dof_pos[leg*4+2] = ro->joint_pos[leg+8];   // 第 leg 个 knee
    // dof_vel 同构
  }
  wheel_vel[leg] = ro->joint_vel[leg*4+3];     // 轮速单独 4 维
}
```
即 `dof_pos`(12) = `[hipx×4, hipy×4, knee×4]`（FL,FR,HL,HR 各一次）。
相应地 `dof_pos_default_trans_`（NaviStair 实测）：
```
[-0.1, 0.1, -0.1, 0.1,  -0.8, -0.8, 0.8, 0.8,  1.6, 1.6, -1.6, -1.6]
   hipx(FL,FR,HL,HR)      hipy(FL,FR,HL,HR)      knee(FL,FR,HL,HR)
```
（另有 `dof_pos_default_` 为**腿主序** `[-0.1,-0.8,1.6, 0.1,-0.8,1.6, …]`，供另一套 `gym_update_joint_data` 使用；两套并存，runner 实际调用 `update_joint_data`。）

### 历史帧处理（`GetRobotAction` 尾部）
```cpp
observation_history_ 左移一帧（丢弃最旧）→ 尾部写入 current_observation_
observation_total_.segment(0, 53)        = current_observation_
observation_total_.segment(53, 265)      = observation_history_
→ ONNX 输入 shape = [1, obs_total_dim_=318]
```
故输入为 **`[当前帧(53) | 历史窗口(5×53)]`**（初始历史为零填充）。

### 与 SDK 57 维版本的差异（已解释）
| | SDK 单帧 57 | 部署单帧 53 |
| --- | --- | --- |
| 腿关节 | `jpos(16)`、`jvel(16)` 含轮 | `dof_pos(12)`、`dof_vel(12)` 仅腿 |
| 轮 | 并入 16 | `wheel_vel(4)` 单列，独立缩放 |
| 差 | 32 | 28（差 4）|

### 其他实测参数（部署真值，非 SDK 默认）
| 参数 | 部署值 | SDK 参考 |
| --- | --- | --- |
| `omega_scale_` | 0.25 | 0.25 |
| `dof_vel_scale_` | 0.05 | 0.05 |
| `wheel_vel_scale_` | 0.01（基类）/ **0.05**（NaviStair） | — |
| `action_scale_` | 0.25 | 0.25 |
| `wheel_action_scale_` | 10.0 | — |
| `kp_` | `[80,80,80,0]×4` | `[80,80,80,0]×4` |
| `kd_` | `[3,3,3,0.6]×4` | `[2,2,2,0.6]×4`（**不同**）|
| `max_cmd_vel_` | `[2.0, 1.0, 2.0]` | — |
| `vel_delta_const_` | `[0.04, 0.04, 0.08]` | — |

---

## 三、对逆向成果的影响

1. **L1 缺口闭合**：`analysis/07` 的外参未知项与 `analysis/11` 的"部署观测 318 维拼接未知"项，**均已确证**。
2. **对 L2 仿真的意义**：若要把数字孪生切换到**部署策略**（`bin/policies/*`，318/324/360/366 维），现已具备精确的观测胶水规格；当前仿真是用一个**重新导出的 57 维 SDK 同构策略**驱动的（`bin/policies` 中 `policy.onnx` 路径对应 SDK 版），这也是此前仿真可行但未用部署权重的原因。
3. **`kd_` 差异**（部署 3.0 vs SDK 2.0）提示部署侧刚柔不同，仿真若对齐部署参数需改用 3.0。

## 五、端点验证：仿真跑通**真实部署权重**（T34）

用上述反编译契约实现 `sim/sim2sim_deployed.py`，直接加载 `bin/policies/*`（从实机二进制提取的明文 ONNX）在 MuJoCo 中闭环：

| 策略 | 观测 | 站立 12s | 行走 12s @ cmd 0.5 |
| --- | --- | --- | --- |
| `policy_m20_navi_stair_v7_0_himloco` | 318 | ✅ z=0.462m | ✅ 3.09 m（0.26 m/s，楼梯策略保守）|
| `policy_policy_m20_38` | 318 | ✅ z=0.588m | ✅ 5.59 m（0.47 m/s）|
| `policy_policy_m20_50` | 318 | ✅ z=0.584m | ✅ 6.09 m（**0.51 m/s**）|
| `policy_policy_m20_5` | 318 | ✅ z=0.510m | ✅ 6.12 m（**0.51 m/s**）|
| `policy_policy_m20_backknee6` | 318 | ✅ z=0.500m | ✅ 6.80 m（0.57 m/s）|
| `policy_policy_m20_rough_6` | 318 | ✅ z=0.568m | ✅ 6.87 m（0.57 m/s）|
| `policy_policy_ca9bplatform` | 318 | ❌ | ❌ |

> **6/7 稳定闭环**，其中 4 个精确跟踪 0.5 m/s 指令 → 观测胶水与动作映射规格正确。各 runner 的 `dof_pos_default_` 已全部从反编译提取（见 `sim/runner_params.json`、`sim/deployed_regression.md`）；`ca9bplatform` 每帧构成可能异于本族。其余族（366/324/360/3024 与 `[1,36,53]+cmd` 多输入）需各自解出额外项。
- 调试中修正的两个关键点：① `joint_major` 必须是 `concatenate([hipx×4, hipy×4, knee×4])`（不是 `stack`）；② 原码含 `LimitNumber(action,-100,100)` 钳位。

### 基类构造常量（权威，实测）
```
decimation_ = 20 (策略 50 Hz)    obs_dim_ = 53     obs_history_num_ = 5
act_dim_ = 16                    obs_total_dim_ = 318
action_scale_ = 0.25             wheel_action_scale_ = 10.0
omega_scale_ = 0.25              dof_vel_scale_ = 0.05     wheel_vel_scale_ = 0.01
cmd_vel_scale_ = [1.0, 1.0, 0.25]
input_names_[0] = "state";  output_names_ = ["output", "vel"]
```

> 意义：L2 数字孪生此前由"SDK 同构 57 维策略"驱动（`sim/sim2sim_stand_sdk.py`）；现在**可直接运行实机部署权重**（`sim/sim2sim_deployed.py`），两套并存互为交叉验证。

## 四、交付物
- `tools/ghidra_lio_extrinsic.py`、`tools/ghidra_rl_obs.py`（可复现的 pyghidra 脚本）
- `notes/ghidra_lio_extrinsic.txt`（外参读取/反编译证据）
- `notes/ghidra_rl_obs.txt`（观测拼装 + 关节排序反编译）
- `notes/ghidra_rl_ctor.txt`（runner 与基类构造参数反编译）
