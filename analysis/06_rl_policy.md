# 06 · RL 部署侧还原（T23）

## 1. 结论

运控核心是**端到端 RL 策略**（非 MPC/WBC），由 `rl_deploy` 以 ONNX Runtime 推理。
- 策略网络：**MLP 57 → 512 → 256 → 128 → 16**，激活 **ELU**（`Gemm/Elu` 共 7 节点，8 个权重张量）。
- 由 PyTorch 2.7.0 导出，ONNX ir_version 8、opset 18；输入名 `obs` `[1,57]`，输出名 `actions` `[1,16]`。
- 部署二进制内嵌 ONNX Runtime **1.20.0**（`share/rl_deploy/lib/onnxruntime/libonnxruntime.so.1.20.0`）；官方 SDK 另带 1.22.0（arm/x86）。

## 2. 观测向量（57 维，逐维定义）

来源：`run_policy/m20_policy_runner.hpp::getRobotAction`，拼接顺序：
```
obs = [ base_omega(3)*0.25 , projected_gravity(3) , command(3) , joint_pos_rl(16) , joint_vel_rl(16)*0.05 , last_action(16) ]
```
| 段 | 维度 | 定义 | 归一化/缩放 |
| --- | --- | --- | --- |
| 1 | 3 | IMU 角速度 `ro.base_omega`（机体系 ωx,ωy,ωz） | ×**0.25** (`omega_scale_`) |
| 2 | 3 | 投影重力 `R^T·[0,0,-1]`（`base_rot_mat.inverse()*g`） | 无 |
| 3 | 3 | 速度指令 `[forward_vel_scale, side_vel_scale, turnning_vel_scale]` | 由手柄/App 直接给定 |
| 4 | 16 | 关节位置（policy 顺序，**轮位清零**）减去默认位 | `joint_pos_rl -= dof_default_policy` |
| 5 | 16 | 关节速度（policy 顺序） | ×**0.05** (`dof_vel_scale_`) |
| 6 | 16 | 上一步动作 `last_action` | 无 |

合计 3+3+3+16+16+16 = **57**。

## 3. 动作向量（16 维）与缩放

```
for i in 0..15:
  tmp[i] = action[policy2robot_idx[i]] * action_scale_robot[i]
tmp += dof_default_robot
腿(i*4..i*4+2, i=0..3): goal_joint_pos = tmp      # 位置控制
轮(i*4+3):              goal_joint_vel = tmp      # 速度控制
```
- `action_scale_robot = {0.125,0.25,0.25,5.0}` ×4（fl,fr,hl,hr 各一组；顺序为 robot 顺序 hipx,hipy,knee,wheel）。
- `dof_default_eigen_robot = [0,-0.6,1.0,0, 0,-0.6,1.0,0, 0,0.6,-1.0,0, 0,0.6,-1.0,0]`（robot 顺序）。
- `dof_default_eigen_policy = [0,-0.6,1.0, 0,-0.6,1.0, 0,0.6,-1.0, 0,0.6,-1.0, 0,0,0,0]`（policy 顺序，12 腿角 + 4 轮 0）。

**关节顺序（关键）**
- `robot_order`（真实/URDF 顺序，按腿分组）：
  `fl_hipx, fl_hipy, fl_knee, fl_wheel, fr_hipx, fr_hipy, fr_knee, fr_wheel, hl_hipx, hl_hipy, hl_knee, hl_wheel, hr_hipx, hr_hipy, hr_knee, hr_wheel`
- `policy_order`（策略输入/输出顺序，先 12 腿角再 4 轮）：
  `fl_hipx,fl_hipy,fl_knee, fr_hipx,fr_hipy,fr_knee, hl_hipx,hl_hipy,hl_knee, hr_hipx,hr_hipy,hr_knee, fl_wheel,fr_wheel,hl_wheel,hr_wheel`
- 两序之间用 `generate_permutation` 生成 `robot2policy_idx` / `policy2robot_idx` 做重排。

## 4. PD 增益与控制频率

- 策略态关节增益：`kp = [80,80,80,0]×4`，`kd = [2,2,2,0.6]×4`（轮位 kp=0、kd=0.6 → 纯速度环）。
- 策略频率：`SetDecimation(4)`，主循环 5ms → 策略 **50Hz**（`agent_timestep=0.02`）。
- 推理线程：`PolicyRunner()` 每 100µs 轮询 `state_run_cnt_ % decimation==0` 触发一次；`session_options_.SetIntraOpNumThreads(4)`，图优化 `ORT_ENABLE_EXTENDED`。
- 运行参数：`rl_deploy` 以 `chrt 90 taskset -c 4,5` 启动（SCHED_FIFO 90，绑定核 4/5）。

## 5. 权重资产

- 文件：`dump/hostA/home_user/sdk_deploy/src/M20_sdk_deploy/policy/policy.onnx`（785,189 B）。
- 张量：`actor.0.weight[512,57] / .bias[512]`、`actor.2.weight[256,512]/.bias[256]`、`actor.4.weight[128,256]/.bias[128]`、`actor.6.weight[16,128]/.bias[16]`。
- 可用 onnxruntime 直接推理（已验证：零输入 → 16 维动作）。
- 训练侧（奖励/课程/域随机化）不在设备上，属推迟项。

## 6. 与部署二进制的交叉

`share/rl_deploy/bin/rl_deploy`（94MB）内嵌 onnxruntime；需确认其加载的 policy 与 SDK 版本一致（由运行时 dump 观测，属 M2 阶段）。SDK `pt_to_onnx.py` 说明权重由 PyTorch `actor` 导出。
