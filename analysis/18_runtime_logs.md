# 18 · 运行时日志证据（T10/T21/T24/MISC）

来源：机上 `rob_bag/20260916.tar.bz2` 解出的各模块日志（本地副本 `captures/csv/20260916/log/`）。
这些日志是**设备自产的真值**，用于交叉验证静态结论。

## 1. 完整 FSM 生命周期（T21 运行时验证）

`rl_deploy.2026_0916.log` 记录了一次完整的开机→站立→RL→趴下→阻尼闭环：

```
13:42:53.343 [StateMachine] start logging!!!
13:42:53.343 [StateMachine]  ------------> start_damping      (上电进入启动阻尼)
13:58:09.132 [StateMachine] idle_state    ------------> standup_state
13:58:12.133 [StateMachine] standup_state ------------> rl_control   (站立≈3s)
17:54:31.582 [StateMachine] rl_control    ------------> liedown_state
19:11:24.381 [StateMachine] liedown_state ------------> joint_damping
```
→ **运行时状态名与 DWARF 枚举完全一致**（`idle_state / standup_state / rl_control / liedown_state / joint_damping`），T21 结论获运行时确证。

## 2. ECAN 总线与固件版本

```
[ECAN_HWI] CA9B is using Ecan Hardware Interface
[Motoreth1] ECAN Program Version: 3.1.6
[Motoreth1] ECAN Compile Date: Mar 16 2026 / Time 13:42:27
[Motoreth1] ECAN Git Commit ID: V2.0.15_9f08d7e5dc341ede
[Motoreth1] ECAN Git Commit Date: Sun Feb 8 22:45:05 2026 -0800
[Motoreth1] MoterTemp : 130        (WARN)
```
→ 与机上固件文件名 `ecan_V2.0.15_9f08d7e5dc341ede.bin` **完全对应**，确认总线实现与固件版本。

## 3. 授权/加密链

```
[EncryptionCheck] 读取授权码文件失败: toml::parse: file open error -> ../conf/SDK_authority_code.toml
[EncryptionCheck] 解析的SN: a9fa1fde70894cf6      ← 与 device-tree serial 一致
[SDK_Mode] SDK模式未授权
[DeviceControl] encryptionCheck success, version: PRO
```
→ 存在 `SDK_authority_code.toml` 授权机制；`encryption_node`(GOS/104) + `/encryptionCheck`(srv) 构成授权链；SN 与 `robot_hardware_info.toml` 一致。

## 4. 实时性与超时（性能特征）

```
[Networketh1] send Data update timeout, delta time is +69.68
[ECAN2DDS] handleMotorData timeout, delta time is +68.68
[ECAN2DDS] DDS_CMD topic data update timeout 0.100066
[MOTION_STATUS] Status Error, Transfer to Joint Damping !!!
[MOTION_STATUS] 系统首次启动：MotionInfo 通道正常，无需重建
```
→ 印证：① ECAN↔DDS 桥有**超时保护**（超时即转 JointDamping）；② `/JOINTS_CMD` 期望 ~100ms 级新鲜度；③ 关节使能需先“清错”。

## 5. rl_deploy 数据记录器

```
[Snapshot] The snapshot recording time window is 300 seconds
[DATA_RECODER] DataRecorder started with 1 second interval
```
→ 对应 CSV `snapshot_*.csv`（1Hz 快照、300s 窗口）与 `20260916_190351.csv`（高频流）；即 `DataStreaming` 实现。

## 6. Basic_server 与 LIO

```
[MAIN] Basic server start / configBase toml Version:1.1.2
[DeviceControl] 从配置中读取跟随模式配置:0
[PowerManagement] 自动进入单电池模式 使能设置:1
[VelControl] 自动首次站立标零:0
[DeviceControl] encryptionCheck success, version: PRO

[lio] ------- Lidar Imu Odometry -------
[lio] LIO version: 1.0.13          ← 与 change_log.md 的 v1.0.13 一致
[node] 里程计节点完成初始化
[udp_sender] UDP server listening on port 30100   ← 印证点云 UDP 旁路端口
```
→ LIO 版本、UDP 30100、Basic_server 配置项全部与静态分析吻合。
