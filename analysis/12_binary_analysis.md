# 12 · 二进制静态分析与策略提取（T14 / T21 / T22 / T23）

工具：REA 6.4.0（`analyze --provider ghidra`，Ghidra 12.1.4；`sha256` 绑定 Evidence）+ 本地 `nm/strings/readelf`。

## 1. 主控二进制定位（T14）

| 二进制 | 大小 | 符号 | 结论 |
| --- | --- | --- | --- |
| `share/rl_deploy/bin/rl_deploy` | 94,505,688 | **未剥离**，17910 符号，含 DWARF | 运控主程序（FSM + 策略推理 + ECAN 接口 + DDS） |
| `share/basic_server/bin/basic_server` | 3,182,136 | 未剥离，11513 符号 | 导航/运动服务端（6687 procedures / 12115 strings，REA 已入库） |
| `share/height_map_nav/bin/height_map_nav` | 1,555,240 | 未剥离，7233 符号 | 高程图导航 |
| `share/lio-perception/bin/lio_ddsnode` | 2,017,520 | **已剥离** | LIO/SLAM（需 Ghidra 反编译） |
| `share/ecan_master/bin/ecan-master` | — | **已剥离** | ECAN 主站 |
| `share/node_driver/bin/*` | — | 未剥离（ctrlmcu 5684 / cpu 5316 / rslidar 7487 / encryption 5121） | 传感器与下位机驱动 |
| `bin/mcu_control`, `bin/mcu_update` | 1.8/2.1MB | 未剥离（~390 符号） | MCU 控制/升级 |

> 结论：**官方运控二进制未去符号、未混淆（无 OLLVM 迹象）**，R2 风险显著低于预期；仅 `lio_ddsnode`/`ecan-master`/`FirmwareAssistant`/`DriverOTA` 剥离符号。

sha256（`bin/rl_deploy`）= `59aa77a24cf42304abf017e5995b6b1997a92c41d7df5dcd2989db1b9662ece8`

## 2. 运控 FSM（T21）— 部署版为 SDK 的超集

命名空间 `qw_m20`（SDK 为 `qw`）。状态类（12 个）：

```
IdleState · StandUpState · RLControlState · LieDownState · JointDampingState · CarMoveState
SdkControlState · ZeroCalibrationState · JointTestState · StartDampingState · ChargeLiedownState
（+ 驱动类 M20StateMachine）
```
字符串常量确认状态名：`idle_state, standup_state, rl_control, joint_damping, liedown_state, car_move, sdk_control, joint_test, start_damping`。

转场入口：`qw_m20::M20StateMachine::GetStateControllerPtr(types::StateName)`（`0xafe08`）、`M20StateMachine::Start()`（`0x149b0c`，大小 0x2610）。SDK 版语义（Idle→StandUp→RLControl→LieDown/JointDamping）在部署版中一致，另增：`SdkControlState`（外部 SDK 接管，对应 `/SDK_MODE` 服务）、`CarMoveState`（轮式行走）、`ZeroCalibrationState`（零位标定）、`JointTestState`、`StartDampingState`、`ChargeLiedownState`（充电趴下）。

## 3. 策略运行器库（T22）— 14 个 gait/mode

符号 `*Runner`（全部驻留在 `rl_deploy`）：

```
M20BasicFlatRunner      M20BasicPlatRunner     M20BasicStairRunner    M20BasicBackkneeRunner
M20NaviFlatPolicyRunner M20NaviStairRunner     M20NaviOrienteerRunner M20NaviChargePolicyRunner
M20ExtrePolicyRunner    M20StandPolicyRunner   M20SixAxisStandRunner  M20FinetuneStandRunner
M20HeightGapPolicyRunner M20StepMoveRunner
```
共性接口：`GetRobotAction(RobotBasicState, UserCommand)`、`cal_command(...)`、`updateCommand(...)`。
→ 说明运控是 **多策略库 + 状态机选策略**，对应地形/任务：平地(flat)、平台(plat)、楼梯(stair)、反膝(backknee)、导航平地/楼梯/越野/充电(navi_*)、极端(extre)、站立/六轴站立/Six-axis、微调站立、高差(height gap)、移步(step move)。

## 4. 内嵌 RL 策略权重（T23 关键成果）

`rl_deploy` 的 `.data` 中以符号形式内嵌 **15 个 ONNX 模型**，已按 vaddr→file offset 精确提取（工具 `tools/extract_policies.py`，产物 `bin/policies/*.onnx`，清单 `bin/policies/policies_report.json`）：

| 符号 | 体积(B) | 输入 | 输出 | 节点 |
| --- | --- | --- | --- | --- |
| `__policy_policy_m20_5_` | 993,320 | `state[1,318]` | `output[1,16]`,`vel[1,3]` | 37 |
| `__policy_policy_m20_38_` | 993,320 | `state[1,318]` | 同上 | 37 |
| `__policy_policy_m20_50_` | 993,320 | `state[1,318]` | 同上 | 37 |
| `__policy_policy_m20_backknee6_` | 993,320 | `state[1,318]` | 同上 | 37 |
| `__policy_policy_m20_rough_6_` | 993,320 | `state[1,318]` | 同上 | 37 |
| `__policy_m20_navi_stair_v7_0_himloco_` | 994,096 | `state[1,318]` | 同上 | 39 |
| `__policy_policy_ca9bplatform_` | 995,165 | `state[1,318]` | 同上 | 57 |
| `__policy_m20_navi_flat_v4_2_` | 998,704 | `state[1,324]` | 同上 | 39 |
| `__policy_m20_navi_charge_v3_29_` | 1,026,352 | `state[1,360]` | 同上 | 39 |
| `__policy_m20_flat_v1_4_` | 1,032,029 | `state[1,366]` | 同上 | 57 |
| `__policy_m20_forward_policy_2_` | 2,080,364 | `state[1,36,53]`,`command[1,5]`,`uncertain[1,1]` | `output[1,16]` | 88 |
| `__policy_m20_finetune_forward_` | 2,101,047 | `state[1,36,53]`,`command[1,13]`,`uncertain[1,1]` | `output[1,16]` | 90 |
| `__policy_m20_finetune_stand_15kg_` | 2,121,527 | `state[1,36,53]`,`command[1,21]`,`uncertain[1,1]` | `output[1,16]` | 90 |
| `__policy_m20_sixaxis_stand_` | 2,121,527 | `state[1,36,53]`,`command[1,21]`,`uncertain[1,1]` | `output[1,16]` | 90 |
| `__policy_m20_hmap_motion_v0_2_` | 3,813,541 | `state[1,3024]` | `output[1,16]` | 64 |

**与官方 SDK 版策略的差异（重要）**
- SDK `policy.onnx`：单帧观测 `obs[1,57]`，纯 MLP（Gemm/Elu），输入名 `obs`。
- 部署版：多数为 **历史堆叠观测** `state[1, 318]`，且 **318 = 6 × 53**（6 帧 × 53 维/帧）；另有 324(=6×54)、360(=6×60)、366(=6×61) 变体对应“per-frame 特征数不同”的模型；带 `command`/`uncertain` 输入的为大策略（含时序结构，节点 88–90）。
- 双输出模型同时给出 `output[1,16]`（关节目标）与 `vel[1,3]`（基座速度估计），说明策略内含或并行输出速度。

其余旁证：policy runner 相关字符串 `../policy/p50_common.pt`、`basic_flat_policy_`、`basic_plat_policy_`、`basic_stair_policy_`、`basic_backknee_policy_`、`common_policy_p_gain_/d_gain_`、`common_policy_path_`。

## 5. rl_deploy 的 DDS 接口（实测字符串）

订阅/发布：`/JOINTS_CMD`、`/JOINTS_DATA`、`/IMU_DATA`、`/IMU_DATA_BODY`、`/IMU_DATA_LEG`、`/MOTION_STATE`、`/MOTION_STATUS`、`/MOTION_INFO`、`/STEER`、`/REAL_STEER`、`/BATTERY_DATA`、`/FAULT_STATUS`、`/HES_STATUS`、`/HEIGHT_IMAGE`、`/SDK_MODE`(服务)、`/BATTERY_CHARGE_ENABLE`。

相关类：`DdsInterface`、`CA9BHardwareInterface`、`EcanHardwareInterface::JointState`、`ecan::Motor`、`ecan::ECAN2DDS`、`MotionDataPublish`、`DataStreaming`(→`WriteDataToCsv`)、`ecan::Snapshot::WirteToFile()`。

## 6. REA 使用记录

- `rea analyze bin/basic_server --provider ghidra` → Evidence `ev_c477264b…`, 6687 procedures / 12115 strings（arm64）。
- `rea inspect-binary-layout` 仅支持 x86-64 ELF，本目标为 aarch64 → 改用 Ghidra provider（记录为工具边界，非失败）。
- APK：`rea inspect-android-package sdk/controlapp.apk`（JADX provider，配置见 `sdk/apk_package.json`）。
- 待做：对 `lio_ddsnode`（剥离）与 `ecan-master`（剥离）跑 Ghidra 反编译（见 §7 待补）。
