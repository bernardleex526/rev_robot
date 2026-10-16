# 19 · T26 导航还原（深度，主机 C/NOS）

来源：主机 C `/opt/robot/share/{slam,global_planner,planner,localization,handler,charge_manager}`（本地 `dump/hostC_opt_robot/`，103 文件）。

## 1. 架构（NOS 主机 = 导航域）

```
建图阶段:         slam_ddsnode ─(LIO+位姿图)─> 点云/栅格地图 ─> map_saver / map_server / occ_grid_file_mapping / construct_full_map
定位阶段:         localization_ddsnode (libLocalization.so) ─> /LOCATION_STATUS, /ODOM(map系)
可通行域:         pcl_pass_grid / pcl_remove ─> /passable_area, /NAV_POINTS
全局规划:         astar_node (Hybrid A*) ─> /path_Astar, /local_goal, /GLOBAL_PLANNER_STATUS
局部规划:         localPlanner (DWA) ─> 速度指令
任务/切换:        handler ─> /planner_mode, /NAV_CMD
充电:             charge_manager + reflective_column_node
```

## 2. 全局规划 = **Hybrid A\***（`config_astar.yaml`）

| 参数 | 值 | 含义 |
| --- | --- | --- |
| `weight_a` / `weight_b` | 1.0 / **1.3** | g 项权重 / 到目标启发式权重（**加权 A\***，非最优但快） |
| `weight_heading` | 0.8 | 朝向与目标一致性 |
| `cost_steer` / `cost_steerchange` | 1.0 / 0.2 | 转弯 / 转向变化惩罚 |
| `cost_gear` / `cost_backward` / `cost_reduce` | 2.0 / 1.5 / 0.85 | 障碍附近 / 倒车惩罚 / g 衰减 |
| `step_size` / `sample_interval` | 0.4m / 0.2m | 节点扩展步长 / 碰撞检测采样 |
| `bodyLength` / `bodyWidth` | 0.45 / 0.45 | 规划的机器人足迹 |
| `max_steer` / `num_steerind` | 0.9 / 3 | 最大转向 / 转向离散数 |
| `goalDis` / `xy_tolerance` | 0.5 / 0.5 | 到点判定 |
| **平滑** | `enable_smoothing=true, smooth_count=7, smooth_degree=3(三次样条), num_samples=7, angle_threshold=60°` | 局部路径样条平滑 |
| 局部目标点 | `local_goal_freq_hz=10.0, max_trajectory_range_=2.0, max_speed_x_=1.0, sharp_turn_angle_=45.0, local_goal_search_window_=10` | 10Hz 选点 |

## 3. 局部规划 = **DWA**（`localplanner.yaml` + `paths/first/`）

- 候选轨迹库：`paths/first/pathList.ply` → **4641 条轨迹 × 10 采样点**（`path_num: 4641, path_sample_num: 10`），`readme.md` 指明由 `dwa_planner.h:127 ReadPathData::readStartPaths()` 读取。
- 覆盖栅格：`X*Y = 90*80`（`pathList`），`correspondences*.ply` 提供轨迹↔栅格对应。
- 机器人/传感器：`robotLength=0.84, robotWidth=0.5, sensorOffset=0`。
- 速度接口（被 Basic_server 覆盖）：`maxSpeedX=1.5, maxSpeedY=0.6, maxTheta=1.0, lookAheadDis=1.5, barking_deceleration=1.0, stop_distance=0.7, max_v_threshold=1.2`。
- 到点/微调：`xy_tolerance=0.1, yaw_tolerance=0.1, dwa_fine_tune_distance=0.5`。
- **DWA 权重**：`weight_goal=1.0, weight_yaw=0.5, weight_spdy=0.2`；障碍 `weight_ob1/2/3=0.6/0.8/1.0`（三层）。
- 障碍检测：`obstacleHeightThre=0.10`，`goal_in_ob_dis=0.25`、`goal_in_ob_z=0.5`；`grid_size_=0.05, grid_occu_num_=2`。
- 模式：`directLine_mode=true`（直线/自主切换）、`change_close=true`、`backward_mode=false`、`judge_turn=false`；`local_try` 控制“仅局部 vs 全局+局部”。

## 4. 话题/服务实现（`config_topic.yaml`，与实测 DDS 图一致）

**订阅**：`/GRID_MAP`(地图)、`/initialpose`(起点)、`/goal_pose`+服务 `/GOAL_GLOBAL`(目标)、`/NAV_POINTS`(可通行点云)、`/ODOM`(定位)、`/CANCEL_NAV`+服务 `/CANCEL_NAV_GLOBAL`、`/planner_mode`(0=直线,1=自主)
**发布**：`/path_Astar`(全局路径)、`/vis_global_points`、`/vis_global_points_pruned`(10Hz)、`/local_goal`(10Hz)、`/local_map`、`/GLOBAL_PLANNER_STATUS`

> 与 `03_middleware_dds.md` 实测话题清单**完全吻合**，闭环验证。

## 5. 点云处理链（可通行域→障碍）

| 阶段 | 二进制 | 参数 |
| --- | --- | --- |
| 外框过滤 | `pcl_pass_grid` | `out[-4,4]×[-4,4]×[-0.30,0.6]`；内框移除机体 `in[-0.45,0.45]×[-0.25,0.25]×[-0.30,0.6]`；离群点去除 `r=0.1, minNeighbors=4`；`leaf_size=0.01` |
| 累积点云清理 | `pcl_remove` | 内框 `in[-0.45,0.45]×[-0.25,0.25]×[-0.4,1.0]`；`leaf_size=0.05`；离群点 `r=0.1, minNeighbors=4` |
| 拼接/建图 | `pcl_concatenate`, `occ_grid_file_mapping`, `construct_full_map`, `crop_map` | — |

## 6. 定位（`conf/params.yaml` + `libLocalization.so` + `include/Localization/*`）

- 组件：`reloc_manager.h`（重定位管理）、`localization.h`、`monitor.h`（退化/失锁监控）、`common.h`。
- 输入含 `dr_lio/*`（`lio.h, so3_math.h, imu_processing.h, use-ikfom.h` —— **与 AOS 侧同一 FAST-LIO/IKFoM 前端**）+ `image_loader.h`（栅格图像加载）。
- 输出：`/LOCATION_STATUS`、`/LOCATION_STATUS/MATCHING_ERROR`（匹配误差）、`/pose_in_apriltag_corrected`（AprilTag 校正）、`/tag_status`。
- 地图格式：`GRID_MAP`(OccupancyGrid) + `.ply` 点云；`drmap` 工具链（`drmap_pack/unpack/apply/edit/show`）负责地图打包/应用。
- 建图模式：`drmap mapping [-i 室内|-o 室外|-n 名称|-b 只建图]`。

## 7. 结论与缺口

- L1 导航条款：**规划器类型（Hybrid A\* 全局 + DWA 局部）、代价权重、速度接口、可通行域参数、重定位机制**均已还原（文件级证据）。
- 缺口：**导航路径偏差 <0.3m 的定量验证**需要“同一地图 + 同一目标点”的实机轨迹；机上录包无运动数据（全为阻尼态），需现场跑或用户提供运动态录包。
- 与既有重构工程 `m20_orignal/src/m20_slam_navigation` 对照：其 `hybrid_astar.cpp`/`dwa_planner.cpp` 与官方参数结构一致，可作 T31 复现起点。
