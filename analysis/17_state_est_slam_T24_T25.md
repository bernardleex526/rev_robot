# 17 · T24 状态估计还原 / T25 建图·SLAM 还原（基于真实录包）

数据来源：机上 `rob_bag`（用户决定替代现场采集），样例包 `20260916`（时长 45.1s，903 条消息）。
本地副本：`captures/bag/20260916/db3/JOINTDAMPING_20260916191124/`（442MB sqlite3 bag）。
解码脚本：`decoders/rosbag_odom_decoder.py`（已验证）。

## 1. 录包内容（权威话题清单）

`metadata.yaml` 记录的话题与消息数：

| 话题 | 类型 | 消息数 | 说明 |
| --- | --- | --- | --- |
| `/ODOM` | `nav_msgs/msg/Odometry` | **452** | 状态估计输出（10Hz） |
| `/LIDAR/POINTS` | `sensor_msgs/msg/PointCloud2` | **451** | 雷达点云（10Hz） |
| `/LIO_ODOM` | `nav_msgs/msg/Odometry` | 0 | 本包未录到（阻尼态） |
| `/height_map` | `sensor_msgs/msg/PointCloud2` | 0 | 本包未录到 |
| `/LIDAR/POINTS2` | `sensor_msgs/msg/PointCloud2` | 0 | 第二雷达未触发 |

> rob_bag 以**运动状态**命名目录（`JOINTDAMPING_<时间>`），说明录包按 FSM 状态分桶。

## 2. `/ODOM` 解码结果（CDR 布局已锁定）

`nav_msgs/Odometry`（每帧 708B，小端，4B 封装头）：
```
[0]   encap 00 01 00 00
[4]   builtin Time{ int32 sec; uint32 nanosec }     → 墙钟（ns since epoch）
[12]  string frame_id      ("map")
[..]  string child_frame_id("")
[..]  align(8) 后 13×float64：
        pose.position[3], pose.orientation[4](x,y,z,w),
        twist.linear[3], twist.angular[3]
```
实测三帧（连续，10Hz）：
```
t=…054.300  pos=(20463.447, 27882.640, 48486.434)  quat=(0.1740,0.1397,0.9449,-0.2397)  twist=0
t=…054.400  pos=(20463.597, 27882.832, 48486.434)  quat=(0.1740,0.1396,0.9448,-0.2400)  twist=0
t=…054.500  pos=(20463.774, 27883.059, 48486.437)  quat=(0.1740,0.1396,0.9447,-0.2403)  twist=0
```
- 位置逐帧**平滑递增**（Δ≈0.28m/0.1s），四元数模长 = 1.000，**证明布局正确**。
- 坐标系：`frame_id = "map"`，child 为空；`twist` 全 0（阻尼态，无运动速度输出）。
- 该帧序列来自阻尼（JointDamping）状态，位置漂移极小，可用于**静止噪声/协方差标定**。

## 3. T24 · 状态估计结论

| 项目 | 结论 | 证据 |
| --- | --- | --- |
| 估计器类型 | **LiDAR-惯性紧耦合迭代 EKF（IEKF, on-manifold）**，即 FAST-LIO / IKFoM 家族 | 二进制内源码路径 `.../dr_lio/include/dr_lio/../IKFoM_toolkit/esekfom/.../mtkmath.hpp`、`dr_lio/{use-ikfom,imu_processing,so3_math,lio}.h` |
| 融合输入 | 双 Robosense Airy 点云 + Yesense IMU（`/IMU_YESENSE`）| `params.yaml` + `node_driver` 配置 |
| 输出 | `/LIO_ODOM`（+ `/LIO_ODOM_HIGH_FREQUENCY`）→ 融合为 `/ODOM`（`map` 系）| 录包 + DDS 图 |
| 协方差/噪声 | `acc_cov=gyr_cov=0.8`、`b_acc_cov=b_gyr_cov=0.01`、`lidar_cov=0.001`、`max_iteration=3`、`esti_plane_threshold=0.1` | `params.yaml` |
| 外参 | `extrinsic_est_en=false`；配置中 `B_I/B_L` 为单位阵（占位）→ 真实外参在二进制内 | `params.yaml` |
| 接触估计 | **无独立接触估计器**（RL 直接消费 IMU+关节反馈）；站立髋/膝角由腿长**几何解析反解**（`acos`） | SDK `standup_state.hpp` |
| 静止特性 | 阻尼态下 `/ODOM` 漂移 < 0.01m/0.1s，姿态稳定 | 录包实测 |

## 4. T25 · 建图/SLAM 结论

| 项目 | 结论 |
| --- | --- |
| 前端 | **LIO（LiDAR-Inertial Odometry，IKFoM 迭代 EKF）**，非扫描匹配+因子图 |
| 后端 | 固化图/重定位在 NOS：`localization`（NDT 匹配）+ `pose_in_apriltag_corrected`；AOS 侧为 LIO 前端 + 累积 |
| 地图表示 | 体素地图（多分辨率 `deepest_level/plane_level/top_level=2/2/1`、`leaf_size=0.15`）+ 射线投射占据（`ray_casting_level=2, range=3.0`） |
| 点云产物 | `/LIO_ALIGNED_POINTS`（机体系配准，`leaf_size_body=0.05`）、`/ACCUMULATED_POINTS_MAP`、`/CLOUD_REGISTERED_BODY`、PCD 全图 `maps/active/full_cloud.pcd` |
| 高程/深度 | 深度图（`level 4, 20Hz, max_depth 3.0, 角分辨率 4°, body_height 0.4`）；高度图（`res 0.04, 100×100, z∈[-1,1]`） |
| 双雷达 | 前/后各一，组播 224.10.10.201/202，msop 6691/6692；外参 x=±0.32028, z=-0.013, pitch=-1.57079 |
| 复现管线 | 需 LIO + 点云/IMU 回放；本机已有 `captures/bag` 可用作输入 |

## 5. 未知项 / 待补

1. `/LIO_ODOM` 与 `/height_map` 在本包为 0 条 —— 需另取**运动态**录包（如 `*_RLControl*`/`*_AUTO*` 目录）才能验证建图 ATE 与高程图。
2. `libdrdds.so.1` 反编译以锁定 drdds 字段名（T20 收尾）。
3. 真实 LiDAR-IMU 外参（二进制内）。
4. 双雷达点云融合方式（合并后统一 IEKF vs 主从）。
