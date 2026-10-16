# 08 · 导航还原（T26）

## 1. 结论

导航为**分层结构**，主要运行在 **NOS(106)** 主机（`localization / passable_area / global_planner / planner / handler / reflective_column / charge_manager`），感知-高程图由 AOS(103) 提供，运动执行由 `rl_deploy` 多策略库完成。

- 地图：**2.5D 高程图/代价栅格**（非纯 2D 占据）；`height_map_nav` 以 0.1m 栅格维护 81×81（局部）窗口，另输出 3D 代价。
- 全局规划：话题 `/path_Astar` 表明**A\*** 类图搜索；`/global_path`、`/GRID_MAP`、`/traversal_cost`。
- 局部规划/跟踪：`/local_path`、`/TRACK_PATH`、`/track_path_baselink`、`/local_goal`、`/goal_baselink`、`/free_paths`、`/local_scans`。
- 速度接口：`/HANDLE_STEER`、`/STEER`、`/REAL_STEER`（drdds/msg/Steer）+ `/NAV_CMD`(NavCmd) —— vx,vy,wz 语义由 `basic_server.toml` 的 `maxSpeedX/maxSpeedY/maxTheta` 约束。
- 重定位：`/LOCATION_STATUS`、`/LOCATION_STATUS/MATCHING_ERROR`（NDT 匹配误差）、`/initialpose`、`/tag_status`(AprilTag)、`/pose_in_apriltag_corrected`。

## 2. 高程图导航参数（`share/height_map_nav/config/height_map_dds.yaml`）

| 组 | 参数 | 值 |
| --- | --- | --- |
| 输入 | `imu_input_topic` / `pcl_input_topic` / `odom_input_topic` | `/IMU_YESENSE` / `/CLOUD_REGISTERED_BODY` / `/LIO_ODOM` |
| 机体 | `robot_height` 0.55, `margin` 0.1 | 机体尺寸基准 |
| 输出范围 | x∈[-4,4], y∈[-4,4], z∈[-1.5,0.5] | 局部高程窗口 |
| 内部范围 | x∈[-0.4,0.4], y∈[-0.2,0.2], z∈[-0.5,0.4] | 机体自遮挡剔除 |
| 体素 | `cloud_now_voxel_leaf_size_xy/z` 0.05；`cloud_local_voxel_leaf_size_xy/z` 0.05 | 点云降采样 |
| 累积/射线 | `accumulation_enabled` true；`ray_casting_enabled` true；`parallel_ray_casting_enabled` true；`ray_tracing_voxel_size` 0.1 | 建模方式 |
| 插值 | `interpolation` false；`interpolation_2d_thresh` 0.4；`interpolation_knear_dis` 0.06；`interpolation_knear` 2 | 空洞补全 |
| 栅格 | `map_resolution` **0.1**；`x_grid_num/y_grid_num` **81×81**；`max_points_per_cell` 30；`map_x_min/y_min` -4.0 | 高程栅格 |
| 障碍 | `obs_min_z` -0.4；`obs_max_z` 0.0；`point_range_flat/stair` 2；`base_gravity_frame` "base_link" | 障碍判定 |
| 地形 | `height_range_single_battery` 0.08；`height_range_flat` 0.25；`height_range_stair` 0.25 | 平/台阶分类阈值 |
| 图像处理 | `cov_kernel_size` 3；`cov_thresh` 0.03；`sobel_thresh` 0.3；`laplacian_thresh` 0.3；`is_open_process_image` true | 粗糙度/坡度（地形分类） |
| 深度图 | `depth_image_inflation_times` 1.0；`included_depth`/`max_depth` 4.0；`cols` 90；`rows` 43；`yaw_step`/`pitch_step` 4 | 深度图膨胀 |

> `height_map_ros.yaml` 另有基于相机的变体（`/royale_cam_.../point_cloud_0`、`/odom`、`default_enable: true`），说明存在 **LiDAR 版**与**相机版（Royale ToF）**两套高程图前端。

## 3. 速度档位与运动模式（`share/basic_server/conf/basic_server.toml`）

- 公共：`maxSpeedY=1.0, maxTheta=1.0, yaw_tolerance=0.1, xy_tolerance=0.1`。
- 模式维度：`AUTO` / `DIRECTLINE`；地形：`FLAT` / `STAIR` / `ORIENTEER`；速度：`LOW_SPEED` / `NORMAL_SPEED` / `HIGH_SPEED`。
- 例（`AUTO.FLAT`）：LOW `maxSpeedX=0.5`、NORMAL `1.0`、HIGH `1.5`；`DIRECTLINE.FLAT`：0.5 / **1.2** / **2.0**；共性参数 `dl_min_yaw≈0.6-0.7`、`barking_deceleration`（急减速）1.3–2.0、`stop_distance`、`dl_min_x/y`、`dl_line_yaw_min`。
- 电源管理：`PowerManagement = {Sleep={time=5,auto=true}, Battery={sigleBatteryMode=true}}`。
- 版本：`Base = {Version="1.1.2"}`。

## 4. 导航话题/服务（NOS 侧重）

**话题**：`/GRID_MAP`,`/LOCATION_STATUS`,`/LOCATION_STATUS/MATCHING_ERROR`,`/global_path`,`/local_path`,`/TRACK_PATH`,`/path_Astar`,`/goal_baselink`,`/local_goal`,`/target_goal`,`/initialpose`,`/traversal_cost`,`/passable_area`,`/impassable_area`,`/free_paths`,`/local_scans`,`/GLOBAL_PLANNER_STATUS`,`/PLANNER_STATUS`,`/NAV_STATUS`,`/NAV_CMD`,`/WEIGHT_ITEMS`,`/planner_mode`,`/GRIDS_ID`
**服务**：`/GOAL_GLOBAL`,`/GOAL_PLANNER`,`/CANCEL_NAV_GLOBAL`,`/CANCEL_NAV_PLANNER`,`/CHANGE_GRID_MAP`(LoadMap),`/NAV_GAIT`,`/CHARGE`,`/CHARGE_GAIT`,`/CHARGE_MOTION_STATE`,`/charge/reflective_column_srv`,`/OAA_ENABLE`,`/OOA_ENABLE`,`/SET_OOA_PARAM`,`/HEIGHT_MAP_ENABLE`,`/HEIGHT_MAP_STAIR_OA_ENABLE`,`/HEIGHT_MAP_TERRAIN_TYPE_CHANGE`

## 5. 与既有重构源码的对照

机上并存用户侧重构工程 `dump/hostA/home_user/m20_orignal/src/m20_slam_navigation/`（源码齐全，**非官方产物**，可作参考/对照）：
`planning/{hybrid_astar, spline_optimizer, motion_primitives, global_planner_node}`、`control/{dwa_planner, line_planner, local_controller_node}`、`localization/{ndt_matcher, eskf, relocalizer, prior_map_loader}`、`terrain/{elevation_grid, traversability_map, step_detector, roughness_analyzer, slope_analyzer}`、`lio/{lio_odometry, imu_processor, voxel_map, point_cloud_deskewer}`、`backend/{loop_closure, factor_graph, pose_graph_optimizer, degeneracy_detector}`、`ros/{drdds_pointcloud_source, drdds_imu_source, native_navigation_bridge, pointcloud_wire}`。
→ 该工程与官方话题/接口（`/path_Astar`、`/traversal_cost`、`/CLOUD_REGISTERED_BODY`、drdds 源）高度吻合，可作为 **T31/T32 的起点**，但仍需以官方二进制/L1 结论为准。

## 6. 未知项

- 全局规划器是否 hybrid A\*（`/path_Astar` 仅表明 Astar 命名）；局部控制器是 DWA / 样条跟踪待确认。
- 代价地图的分类（可通行/障碍/台阶）权重与 `traversal_cost` 语义。
- 落足点规划（轮足）与 `MOTION_STATE`/`GAIT` 的耦合关系。
- NOS(106) 主机的完整进程/话题需单独勘测（见 09 节 + 待办）。
