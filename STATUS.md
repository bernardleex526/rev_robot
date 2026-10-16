# 执行状态报告

生成：M1/M2/M3/M4 全阶段推进后。输出根目录 `/home/lee/rea`。

## 里程碑

| 里程碑 | 状态 |
| --- | --- |
| M0 环境与备份 | ✅ 完成（T01–T05；全盘分块传输已结束 `ALL_IMAGES_DONE`，文件已落盘）|
| M1 静态全貌 | ✅ 完成（T06–T14）|
| M2 运行时录制 | ✅ 完成（T15 授权 → T16/T17/T18 被动采集；T19 用 rob_bag 替代）|
| M3 算法还原 | ✅ 完成（T20–T27，算法/协议/FSM/策略提取全部闭环）|
| M4 数字孪生 | ✅ **完成 (L2 验收全部达标)**（T28–T32 本地闭环复现）|

## 已完成任务 (M4 全量完成)

- **T28 模型整理**：MJCF 原生模型整理 + 2202 网格；导出 `sim/m20_description/urdf/m20.urdf`（17 links, 16 joints）；`check_urdf` 与 `validate_model.py` 均验证通过。
- **T29 策略回放**：15 个内嵌 ONNX 策略全部通过推理测试；双向关节标定误差 $4.4 \times 10^{-16} \text{ rad}$；实机 200Hz 姿态完全落入模型限位。
- **T30 建图复现**：从机上包解码出 **281.85m** 高速运动实测数据（452 帧 `/ODOM` + 451 帧 96 线 `/LIDAR/POINTS`）；本地编译 `m20_slam_navigation`，FAST-LIO 单元测试 7/7 全过。
- **T31 导航复现**：加权 Hybrid A\* 全局规划 + DWA/LinePlanner 局部控制闭环（`sim/nav_sim/nav_closed_loop`），直线、斜向、绕障 3 场景全部通过，平均路径偏差 $< 0.15\text{m}$，零碰撞。
- **T32 运控闭环**：MuJoCo 真实动力学闭环，稳定站立 30 秒（倾角 $< 0.8^\circ$），平稳行走 12 秒 @ 0.44 m/s（倾角 $< 2.7^\circ$），原地旋转平稳。

## 关键成果与交付

1. **L1 知识库**：架构、总线通信（drdds CDR 解码）、FSM（12态20步态）、15 个部署 RL 策略、FAST-LIO 与 Hybrid A*/DWA 完整参数与接口。
2. **L2 数字孪生**：`sim/` 目录下全套可复现脚本、URDF 模型、ROS 2 导航/建图工程、MuJoCo 站立行走验证器。
3. **关键发现**：
   - 实机 bag 并非静止，实际包含 **281.85m** 连续走航数据（平均航速 6.46 m/s）。
   - MJCF 模型角度即为策略 published 逻辑角，无需叠加底层硬件偏置。
   - 导航控制器具备自动航向巡航与避障切换特性。

## 实机在线核验（只读对照）

已连 Wi-Fi，对三机做只读核验（详见 `analysis/23_live_verification.md`）：

- ✅ **8 个关键二进制哈希逐一字节一致**（`rl_deploy`/`basic_server`/`lio_ddsnode`/`astar_node`/`localPlanner`/`localization_ddsnode`/`handler`/ECAN 固件）。
- ✅ 三机拓扑、OS 20.04.6、内核 5.10.198、ROS 2 Foxy + Fast DDS 2.14.0、98 话题/服务、LIO/导航/硬件配置逐项吻合、15 策略提取无误。
- ⚠️ **修正 1**：ECAN **非 EtherCAT**，实为 CAN-FD over Ethernet（`libecanmaster.so` 进程内）。
- ⚠️ **修正 2**：`rl_deploy` 为 **SCHED_RR** 90（非 SCHED_FIFO）。
- ✅ **定案未知项**：双雷达实际生效者为 `rslidar`（速腾），`hsLidar` 零收包；DDS 发布者为裸 DDS 参与者（`_CREATED_BY_BARE_DDS_APP_`）。

## 逆向收尾（T33/T34，实机二进制可证）

- ✅ **T33a LiDAR-IMU 外参**：确证为 **identity**，由 `lio_ddsnode` 硬编码路径的 `params.yaml` 直读、无兜底、无覆盖；物理雷达安装由 `rslidar` 驱动烘焙（前后合并到机身帧）。
- ✅ **T33b 部署观测布局**：**`obs_dim_=53`、`obs_history_num_=5`、`obs_total_dim_=318`**；每帧 = `ω·0.25(3)+重力(3)+cmd·[1,1,0.25](3)+(dof_pos−default)(12,关节主序)+dof_vel·0.05(12)+wheel_vel·scale(4)+last_action(16)`。
- ✅ **T34**：`sim/sim2sim_deployed.py` 用**真实部署权重**闭环——**15 个策略中 14 个完成站立/行走闭环**（含多输入族、步态相位族、软启动与高程图族）；解出**策略↔runner 权威映射**与**7 种观测变体**（A 关节主序 / B 腿主序 / C 步态相位 / D 常量0.52 / E 腿主序+步态+常量1.0 / F 多输入 `state[1,36,53]+command+uncertain=1` / G 高程图 504×6），以及逐 runner 的 `kp/kd/gait_commands` 真值与软启动规则。
- 脚本：`tools/ghidra_lio_extrinsic.py`、`tools/ghidra_rl_obs.py`、`tools/ghidra_policy_map.py`、`tools/parse_runner_params.py`；数据：`sim/runner_params.json`；报告：`analysis/24_obs_layout_extrinsic.md`、`sim/deployed_regression.md`。

## 产物规模

- `/home/lee/rea` ≈ 2.5GB；`analysis/` 22 篇技术文档；`bin/policies/` 15 个策略。
- 镜像目录 `/media/lee/数据/rea_images/`（231/231 分块传输已完成）。
