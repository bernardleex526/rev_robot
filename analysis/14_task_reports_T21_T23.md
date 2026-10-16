# 14 · T21/T22/T23 结论与证据（M3 核心，不依赖人工检查点）

> 这三个任务只依赖 T14（已完成），因此先于 M2 的运行时录制执行。

## T21 · 运控 FSM 与模式切换 —— ✅ 完成

**方法**：`nm --demangle` + DWARF 枚举提取（`tools/dwarf_enums.py`）+ SDK 交叉印证。
**证据**：`bin/rl_deploy_full_symbols.txt`、`bin/rl_deploy_enums_unique.txt`。

- 状态集合（部署版，DWARF 权威）：`kIdle=0, kStandUp=1, kJointDamping=2, kStartDamping=3, kLieDown=4, kSetZero=5, kChargeLieDown=6, kCarMove=16, kRLControl=17, kJointTest=18, kSdkControl=100`。
- 对外运动状态：`WaitingForStand=0 … RLControlMode=17 … DampingLiedown=4097`。
- 步态族（20 个 `RobotGaitType`）：`BasicFlat/Plat/Stair/BackKnee/Stand`、`ExtreForward/Bip/InvBip/Jump`、`NaviCharge/Flat/Stair/Finetune/Orienteer`、`HGap/HStair/DGap`、`SixAxisStand/StepMove/RiseAgain`。
- 状态机入口：`qw_m20::M20StateMachine::{Start,GetStateControllerPtr,Stop}`。
- 状态类：`IdleState, StandUpState, RLControlState, LieDownState, JointDampingState, CarMoveState, SdkControlState, ZeroCalibrationState, JointTestState, StartDampingState, ChargeLiedownState`。
- 切换条件（SDK 语义 + 二进制字符串一致）：L1/R1/R2/L2 键 → 站立/趴下/阻尼/RL；异常 → 阻尼；`safe_control_mode!=0` → 阻尼。
- 急停/泄力路径：`SafeController` → `kJointDamping`；`RLControlState::PostureUnsafeCheck()` 在 SDK 中**被注释禁用**（重要风险提示）。
- 与官方可触发模式**一一对应**（手柄 4 键 + App `G20_KEY_*` + `/SDK_MODE` 服务进入 kSdkControl）。

## T22 · 运控路线判定与核心模块 —— ✅ 完成

**判定：端到端 RL**（有证据链）。

| 证据 | 内容 |
| --- | --- |
| 动态依赖 | `rl_deploy` 的 `NEEDED` 含 **`libonnxruntime.so.1`**（另有 `libdrdds`/`libfastrtps`/`libecanmaster`），**不含任何 QP/MPC 求解器**（qpOASES/osqp/proxsuite/hpipm/crocoddyl/pinocchio 命中数 = 0） |
| 推理调用点 | `Ort::Session::Session(Env const&, void const*, unsigned long, SessionOptions const&)`（**从内存缓冲区加载模型**）、`Ort::Value::CreateTensor<float>`、`Ort::Session::Run` 等 250 个 Ort:: 符号 |
| 内嵌模型 | `.data` 段 15 个 `__policy_*` ONNX 数组，供上述内存加载（对应 §12 提取结果） |
| 无 MPC 特征 | 无 QP 库、无显式代价/约束矩阵；闭环由策略直接输出关节目标/速度 |

**核心模块定位**
- 策略运行器（14 个 `M20*Runner`）实现 `GetRobotAction()`：观测拼接 → ONNX 推理 → 动作反缩放 → 关节指令。
- 底层关节接口：`EcanHardwareInterface::JointState`、`ecan::Motor`（SCHED_FIFO，eth1 EtherCAT）、`ecan::ECAN2DDS`。
- 数据记录/发布：`DataStreaming`（`WriteDataToCsv`）、`MotionDataPublish`、`ecan::Snapshot::WirteToFile()`。
- 触地/接触估计与逆运动学：SDK 侧未暴露独立接触估计器（RL 直接消费 IMU+关节反馈）；`StandUpState` 内的髋/膝角由腿长解析反解（`acos`），属**几何解析 IK**，非接触估计。MPC/WBC 路径不存在。

## T23 · RL 部署侧还原 —— ✅ 完成（权重 + 胶水）

**权重**：15 个策略 ONNX 已提取（`bin/policies/*.onnx` + `policies_report.json`），可用 onnxruntime 直接加载推理；官方 SDK 另提供 57 维 `policy.onnx`。

**胶水层（官方 SDK = 权威可读实现）**：`run_policy/m20_policy_runner.hpp`
- 观测 57 维 = `[ω×0.25 (3), Rᵀg (3), cmd (3), joint_pos_rl-默认位 (16), joint_vel_rl×0.05 (16), last_action (16)]`
- 动作 16 维：`policy→robot` 重排 × `action_scale_robot{0.125,0.25,0.25,5}×4` + 默认位；腿=位置、轮=速度
- `kp=[80,80,80,0]×4`、`kd=[2,2,2,0.6]×4`、decimation 4、50Hz、`chrt 90 taskset -c 4,5`
- 关节顺序：`robot_order`（按腿含轮）↔ `policy_order`（12 腿角 + 4 轮）

**部署版差异（待 M2 运行时确认）**：内嵌策略输入多为 `state[1,318]=6×53`（及 324/360/366），说明部署策略使用**多帧历史堆叠观测**而非 SDK 的单帧 57 维；带 `command`/`uncertain` 输入的时序策略（节点 88–90）另有一套胶水。**结论**：SDK 提供胶水语义骨架，部署版为历史堆叠变体，逐维拼接需运行时 dump 校验（属 T29 回放验证范畴）。

## 结论对 L1 验收的贡献

- ③ FSM 一一对应 —— **达成**（枚举级证据）。
- ④ 运控路线定性 + RL 观测/缩放 —— **达成**（SDK 逐维定义 + 部署权重提取 + 无 MPC 证据）。
