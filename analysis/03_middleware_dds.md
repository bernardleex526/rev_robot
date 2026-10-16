# 03 · 中间件：ROS 2 Foxy + Fast DDS

## 1. 结论

- 中间件为 **ROS 2 Foxy**（`/opt/ros/foxy`），RMW = **Fast DDS**（`libfastrtps.so.2.14.2`、`libfastcdr.so.2.2.5` 位于 `/opt/robot/lib`）。
- 进程间同时使用 **UDPv4** 与 **共享内存(SHM)** 传输；`/dev/shm/fast_datasharing_*` 文件即为 Fast DDS SHM 段（实测存在，命名含各 participant GUID）。
- 自定义消息包：**`drdds`**（云深处封装），带自定义服务，如 `drdds/msg/JointsDataCmd`、`drdds/srv/StdSrvInt32`。SDK 附带 `samples/drdds-ros2/` 示例（joints/lidar/service/params/action）。
- ROS_DOMAIN_ID 未显式设置（= 默认 0）；官方 SDK 文档在仿真时另用 `ROS_DOMAIN_ID=1`。

## 2. `fastdds.xml`（`/opt/robot/fastdds.xml`）

```xml
<transport_descriptors>
  <transport_descriptor>
    <transport_id>udp_transport</transport_id><type>UDPv4</type>
    <interfaceWhiteList>
      <address>127.0.0.1</address>
      <address>10.21.33.103</address>   <!-- setup_ros2.sh 按主机追加 .104/.106 -->
    </interfaceWhiteList>
    <sendBufferSize>8388608</sendBufferSize><receiveBufferSize>8388608</receiveBufferSize>
    <maxMessageSize>65500</maxMessageSize><non_blocking_send>true</non_blocking_send>
  </transport_descriptor>
  <transport_descriptor>
    <transport_id>shm_transport</transport_id><type>SHM</type><segment_size>500000000</segment_size>
  </transport_descriptor>
</transport_descriptors>
<participant profile_name="ros2_daemon" is_default_profile="true">
  <rtps>
    <builtin><discovery_config><discoveryProtocol>SIMPLE</discoveryProtocol><EDP>SIMPLE</EDP>
      <simpleEDP><PUBWRITER_SUBREADER>true</PUBWRITER_SUBREADER><PUBREADER_SUBWRITER>true</PUBREADER_SUBWRITER></simpleEDP>
    </discovery_config></builtin>
    <userTransports><transport_id>udp_transport</transport_id><transport_id>shm_transport</transport_id></userTransports>
    <useBuiltinTransports>false</useBuiltinTransports>
  </rtps>
</participant>
```
环境：`FASTRTPS_DEFAULT_PROFILES_FILE=/opt/robot/fastdds.xml`（`setup_ros2.sh` 导出；业务进程自身 environ 中未出现该变量，疑由包装脚本/编译期注入）。

## 3. 直播 DDS 图（实测，只读；`runtime/hostA_dds.txt` 为完整 170 行）

发现方式：`HOME=/dev/shm/ros_home`（tmpfs，避免写狗盘）+ `ros2 topic/service/node list --no-daemon`。

### 3.1 关键话题（按链路归类）

**运控/状态（drdds）**
`/JOINTS_DATA`, `/JOINTS_DATA_10HZ`, `/JOINTS_CMD`, `/IMU_DATA`, `/IMU_DATA_10HZ`, `/MOTION_STATE`, `/MOTION_INFO`, `/MOTION_STATUS`, `/GAIT`, `/STEER`, `/REAL_STEER`, `/HANDLE_STEER`, `/BATTERY_DATA`, `/FAULT_STATUS`, `/EXCEPTION_NOTIFICATION`, `/LED/STATUS`, `/CPU_103`, `/CPU_104`, `/CPU_106`, `/dr/MotionInfo`

**感知（标准 ROS 消息）**
`/LIDAR/POINTS`, `/LIDAR/POINTS2`, `/LIDAR/IMU201`, `/LIDAR/IMU202`, `/LIDAR/STATUS`(drdds/AiryLidarStatus), `/IMU_YESENSE`, `/IMU`, `/LIO_ODOM`, `/LIO_ODOM_HIGH_FREQUENCY`, `/LIO_ALIGNED_POINTS`, `/ACCUMULATED_POINTS_MAP`, `/CLOUD_REGISTERED_BODY`, `/LOC_BODY_POINTS`, `/DEPTH_POINTS`, `/DEPTH_IMAGE`, `/HEIGHT_IMAGE`, `/height_map`, `/grid_map`(grid_map_msgs), `/grid_map_3d`

**导航（NOS）**
`/GRID_MAP`(OccupancyGrid), `/LOCATION_STATUS`, `/LOCATION_STATUS/MATCHING_ERROR`, `/global_path`, `/local_path`, `/TRACK_PATH`, `/path_Astar`, `/goal_baselink`, `/local_goal`, `/target_goal`, `/initialpose`, `/traversal_cost`, `/passable_area`, `/impassable_area`, `/free_paths`, `/GLOBAL_PLANNER_STATUS`, `/PLANNER_STATUS`, `/NAV_STATUS`, `/NAV_CMD`, `/WEIGHT_ITEMS`, `/planner_mode`, `/GRIDS_ID`

**外设/扩展**
`/GPS`(drdds/NavSat), `/FIBOCOM/net_rtk/gngga`, `/FIBOCOM/net_rtk/heading`, `/fibo_fusion_pose`, `/fibo_fusion_state`, `/UWB_*`, `/tag_status`, `/pose_in_apriltag_corrected`, `/CHARGE_*`, `/charge/reflective_column_srv`, `/HES_STATUS`, `/OOA_STATUS`, `/TERRAIN_CLASSIFIER_STATUS`, `/SEG_CLOUD`

### 3.2 服务（节选）

`/SDK_MODE`(StdSrvInt32, 切换 SDK 接管关节数据流, 命令 200=200Hz, 0=退出), `/LIO_ENABLE`, `/HEIGHT_MAP_ENABLE`, `/HEIGHT_MAP_STAIR_OA_ENABLE`, `/HEIGHT_MAP_TERRAIN_TYPE_CHANGE`, `/OOA_ENABLE`, `/SET_OOA_PARAM`, `/NAV_GAIT`, `/CHARGE`, `/CHARGE_GAIT`, `/CHARGE_MOTION_STATE`, `/GOAL_GLOBAL`, `/GOAL_PLANNER`, `/CANCEL_NAV_GLOBAL`, `/CANCEL_NAV_PLANNER`, `/CHANGE_GRID_MAP`(LoadMap), `/LIDAR/GET_INFO`, `/LIDAR/POWER`, `/JOINTS/POWER`, `/GPS/POWER`, `/VIDEO/POWER`, `/FAN/SPEED`, `/FAN/STATUS`, `/LED/*`, `/EXT_LOAD/*`, `/FP/POWER`, `/set_service`(SetParam), `/encryptionCheck`(StdSrvString)

> 说明：`ros2 node list` 仅枚举到 4 个节点（`/accumulate_cloud`、`/exception_subscriber_node`、`/message_subscriber_node`、`/passable_area`），说明多数业务节点使用**非标准 DDS participant 配置**（或在各自 netns），其话题仍可通过发现服务枚举。这是当前的一个**未知项**（见 11 节）。

## 4. 点云 UDP 旁路接口

`lio-perception/conf/params.yaml` → `accumulated_points.udp_output`: 端口 **30100**，分辨率 0.2m，按键值为“请求-响应”模式（`update_yaml.py`/`register_conf.sh` 可改配置）。
另：`basic_server` 监听 **30001 / 30002**（TCP），`mediamtx` 提供 RTSP **8554** / RTMP **1935** / HLS **8888/8889** / **9393**。
