# 05 · 运控状态机（FSM）与模式切换

## 1. 结论

运控为**分级结构**：
- 上层任务/模式状态机：`qw::QwStateMachine`（`StateMachineBase` 派生），5ms tick。
- 执行层：每个状态对应一个 `StateBase` 派生控制器；RL 态内部再起一个策略线程（100µs 轮询、按 decimation 触发推理）。
- 底层：`SafeController`（安全/失能）、`RobotInterface`（DDS↔关节）、ECAN 关节阻抗。

## 2. 状态枚举（官方 SDK = 真值）

`include/types/custom_types.h`：
```cpp
enum RobotMotionState { WaitingForStand=0, StandingUp=1, JointDamping=2, LieDown=4, RLControlMode=6 };
enum StateName { kInvalid=-1, kIdle=0, kStandUp=1, kJointDamping=2, kLieDown=4, kRLControl=6 };
enum RemoteCommandType { kKeyBoard=0, kGamepad };
enum KeyCode { L1, L2, R1, R2, UNKNOWN };
enum RobotName { M20 = 11 };
enum RobotType { QuadrupedWheel = 1 };
```

## 2b. 部署版枚举（★ 权威，DWARF 提取，工具 `tools/dwarf_enums.py`）

从 `bin/rl_deploy` 的 DWARF 直接读出（`bin/rl_deploy_enums_unique.txt`）：

```cpp
enum StateName {            // 部署版（12 态）
  kInvalid=-1, kIdle=0, kStandUp=1, kJointDamping=2, kStartDamping=3, kLieDown=4,
  kSetZero=5, kChargeLieDown=6, kCarMove=16, kRLControl=17, kJointTest=18, kSdkControl=100 };

enum RobotMotionState {     // 对外运动状态（11 值）
  WaitingForStand=0, StandingUp=1, JointDamping=2, StartDamping=3, LieDown=4, SetZero=5,
  CarMove=16, RLControlMode=17, JointTest=18, SdkControlMode=100, DampingLiedown=4097 };

enum RobotGaitType {        // 步态/策略族（20 个）
  BasicFlat=4097, BasicPlat=4098, BasicStair=4099, BackKnee=4100, Stand=4101,
  ExtreForward=8193, ExtreBip=8194, ExtreInvBip=8195, ExtreJump=8196,
  NaviCharge=12289, NaviFlat=12290, NaviStair=12291, NaviFinetune=12292, NaviOrienteer=12293,
  HGap=20481, HStair=20482, DGap=20483,
  SixAxisStand=61441, StepMove=61442, RiseAgain=61443 };

enum RobotName { X30=0, Lite3=1, P50=2, K1C=3, K1W=10, M20=11 };
enum RobotType { Quadruped=0, QuadrupedWheel=1, QuadrupedArm=2, Humanoid=3 };
```

> **与官方 SDK 的关键差异**：SDK `RLControlMode=6`，部署版 `=17`；SDK 无 `StartDamping/SetZero/JointTest/SdkControlMode/CarMove`。`RobotGaitType` 为部署版独有（SDK 未定义步态枚举）。这说明官方 SDK 是**精简教学版**，设备固件为完整商用版。

## 3. 状态与职责

| 状态 | 类 | OnEnter | Run 行为 | 下一态判定 |
| --- | --- | --- | --- | --- |
| `kIdle` (0) | `IdleState` | `msfb=WaitingForStand` | 读本体数据、做关节/IMU 正常性检查、周期打印；`SetJointCommand(0)`（**泄力**） | 关节异常→kIdle；`target_mode==StandingUp`→**kStandUp** |
| `kStandUp` (1) | `StandUpState` | 记录初始关节位；按 `pre_height=0.12` 由腿长反解髋/膝目标角 | 2s（`stand_duration_`）内插值到站立位（`stand_height=0.38`），角关节位置 PD（kp=200,kd=4），轮 kd=1 | →kRLControl（经 L2） |
| `kRLControl` (6) | `RLControlState` | 起策略线程，`msfb=RLControlMode` | 5ms 采集观测（双缓冲）；策略线程每 `decimation=4` 次→50Hz 推理→`SetJointCommand` | `safe_control_mode!=0`→kJointDamping；`target_mode==LieDown`→kLieDown；否则停留 |
| `kLieDown` (4) | `LieDownState` | `msfb=LieDown` | 2s（`liedown_duration_`）插值回趴下位 | →kIdle |
| `kJointDamping` (2) | `JointDampingState` | `msfb=JointDamping` | 关节阻尼（kp=0，kd 保持），泄力安全态 | 需人工/上层恢复 |

## 4. 主循环（`StateMachineBase::Run`）

```
timer 5ms → spin_some(node) → RefreshRobotData()
          → current_controller_->Run()
          → next = LoseControlJudge() ? kJointDamping : GetNextStateName()
          → 若 next != current：OnExit(); 切控制器; OnEnter();
```
`StateMachineBase` 关键成员：`_dt=0.001`、`set_timer.time_init(5)`、`SafeController`、`RobotInterface`、`UserCommandInterface`、静态 `msfb_`（`MotionStateFeedback`）。

## 5. 触发链路（一一对应官方可触发模式）

| 触发源 | 动作 | 结果状态 |
| --- | --- | --- |
| 手柄 `L1` / App `G20_KEY_L1` | `target_mode=StandingUp` | kIdle→**kStandUp** |
| 手柄 `L2` / App `G20_KEY_L2` | `target_mode=RLControlMode` | kStandUp→**kRLControl** |
| 手柄 `R1` / App `G20_KEY_R1` | `target_mode=LieDown` | kRLControl/kStandUp→**kLieDown**→kIdle |
| 手柄 `R2` / App `G20_KEY_R2` | `target_mode=JointDamping` | 任意→**kJointDamping** |
| 失稳/安全 | `safe_control_mode!=0` 或 `LoseControlJudge()` | →**kJointDamping** |
| 关节/IMU 异常 | `JointDataNormalCheck()!=0`（NaN/超限）| 停留/回 **kIdle** |

## 6. 安全与泄力路径

- **急停/阻尼**：`SafeController`（`include/utils/safe_controller.hpp`）→ kJointDamping；`gamepad_interface` 中 R2 立即置 JointDamping。
- **姿态安全检查**：`RLControlState::PostureUnsafeCheck()` 当前**被注释禁用**（roll>30°/pitch>45° 的翻转保护未生效）——**重要发现**，说明实机翻倒保护不依赖该函数。
- **通信/控制超时**：`RLControlState` 通过 `uc_ptr_->GetUserCommand()->safe_control_mode` 判失联（`heartbeat.hpp` 维护）。
- **关节数据守门**：`IdleState::JointDataNormalCheck()` 检查 NaN、`±0.2rad` 越限、轮速 >`wheel_vel_limit_+0.1`(100.1)、关节速 >`joint_vel_limit_+0.1`。
- **IMU 守门**：`ImuDataNormalCheck()` 检查 rpy/omega 非 NaN 且 ≤π，加速度模长 ∈[0.1g, 3g]。

## 7. 与部署二进制的一致性（REA/Ghidra 结果见 §bin）

在部署二进制 `share/rl_deploy/bin/rl_deploy`（94MB）与 `basic_server` 中检索到与 SDK 一致的状态字符串（`idle_state`/`standup_state`/`rl_control`/`joint_damping`/`liedown_state`）与日志格式，详情见 `analysis/12_binary_analysis.md` 与 `bin/` 产物。
