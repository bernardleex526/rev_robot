# 13 · drdds 消息与服务定义（协议规范，T20 基础）

来源（机上只读拉取，均为生成物）：
- `/usr/local/include/dridl/` → 766 文件，命名空间：`dr_msgs`、`dr_srvs`、`amap_nav_msgs`、`fibocom_msgs`、`piper_msgs`、`vision_msgs`、`nav_msgs`、`sensor_msgs`、`geometry_msgs`、`std_msgs`、`tf2_msgs`、`visualization_msgs`、`builtin_interfaces`
- `/opt/ros/foxy/share/drdds-ros2-msgs/{msg,srv}/*.{msg,srv,idl}` → 本地副本 `dump/hostA/ros_foxy_share/`

> 这些是 ROS2 Foxy + Fast DDS 的 **IDL 生成物**，字段偏移与序列化布局可直接从 `.idl` 推导，用于写解码脚本（M3/T20）。

## 1. 消息（`drdds/msg/*`，共 44 个 msg 文件）

关键结构：

**MetaType（所有 drdds 消息的公共头）**
```
uint64 frame_id
builtin_interfaces/Time stamp     # {int32 sec; uint32 nanosec}
```

**JointsData / JointsDataCmd（关节反馈/指令，16 关节定长）**
```
MetaType header
JointsDataValue data              # JointData[16] joints_data
```
```
JointData:    char[4] name | uint16 data_id | uint16 status_word
              float32 position | torque | velocity | motion_temp | driver_temp
JointDataCmd: char[4] name | uint16 data_id | uint16 control_word
              float32 position | torque | velocity | kp | kd
```

**ImuData**
```
MetaType header; ImuDataValue data
  float32 roll,pitch,yaw; float32 omega_x,y,z; float32 acc_x,y,z
```

**BatteryData**
```
MetaType header; BatteryDataValue[] data
  uint16 voltage(10mV) | int16 current(10mA) | uint16 remaining_capacity(10mAh)
  uint16 nominal_capacity | uint16 cycles | uint16 production_date
  uint16 balanced_low | uint16 balanced_high | uint16 protected_state
  uint8 software_version | battery_level | mos_state | battery_quantity | battery_ntc
  float32[] battery_temperature | char[32] battery_serialnum
```

**MotionState / MotionStatus**
```
MotionState:  int32 state
MotionStatus: uint32 drivers_over_heat | joints_over_heat | joints_pos_error | joints_vel_error
              | joints_data_nan_error | joints_update_error | joints_timeout | driver_status_error
              uint8 hipy_pos_outlimit
              uint64 common_error   # 位域：motion_posture_error, body_posture_error, imu_timeout, imu_nan_error, is_lift...
```

**Steer（手柄/遥操作 6 通道，归一化 [-1,1]）**
```
float32 x(前后) | y(左右平移) | z(上下起伏) | roll(扭身) | pitch(抬头) | yaw(水平转)
```
**NavCmd（导航速度接口）**：`float32 x_vel | y_vel | yaw_vel`
**Gait**：`uint32 gait`
**MotionInfo**：`float32 vel_x,vel_y,vel_yaw,height | MotionState state | Gait gait_state | float32 payload,remain_mile`

其余：`AiryLidarStatus/AiryLidarValue`、`CpuData/CPUStatus`、`MemoryStatus`、`FileSystemStatus`、`NetworkStatus`、`NodeStatus`、`Exception`、`FaultEvent/FaultEventArray/FaultStatus`、`LedStatusLight`、`LocationStatus`、`PlannerStatus`、`NavSat`、`Heartbeat`、`GridID/GridsID`、`StdMsgInt32/StdMsgFloat32`、`Timestamp`、`MetaType`。

## 2. 服务（`drdds/srv/*`）

| 服务类型 | 定义 |
| --- | --- |
| `StdSrvInt32` | Request `int32 command` / Response 状态（`/SDK_MODE`、`/LIO_ENABLE`、`/CHARGE` 等）|
| `StdSrvString` | Request `string` / Response（`/encryptionCheck`、`/LIDAR/GET_INFO`）|
| `StdSrvStringToInt32` | — |
| `SetParam` | `/set_service` |
| `SetOOAParam` | `/SET_OOA_PARAM` |
| `LoadMap` | `/CHANGE_GRID_MAP` |
| `PoseStampedToInt32` | `/GOAL_GLOBAL`、`/GOAL_PLANNER` |
| `DeviceControl` | 外设电源/开关 |
| `JudgeVel` | 速度判定 |

## 3. 序列化要点（写解码脚本时）

- 均以 `MetaType`（8 字节 `frame_id` + 8 字节 `stamp`）开头。
- 定长数组 `JointData[16]` = 16 × (4B name + 2+2B id/status + 5×4B float) = 16 × 28 B = 448 B。
- `char[4] name` 为关节名（如 `fl_hipx_joint` 的前 4 字符或缩写），`char[]` 变长仅出现在 *Value 变体。
- 单位：电池电压 10mV、电流 10mA、容量 10mAh；IMU 弧度制；Steer/NavCmd 归一化。
- 与 ECAN 侧 `JointUnit`（04 节）字段一一对应（`data_id`/`status_word`/`control_word` 贯穿）。

## 4. 覆盖评估（对 T20 的 ≥95% 目标）

- 上述定义覆盖运行图中**全部 drdds 话题/服务**（对照 03 节 170 行清单）。
- 标准 ROS 消息（`sensor_msgs/PointCloud2`、`Imu`、`nav_msgs/Odometry|Path|OccupancyGrid`、`grid_map_msgs/GridMap`、`visualization_msgs/Marker*`、`geometry_msgs/Pose*`）为公开 schema。
- 剩余未知：`fibocom_msgs`、`amap_nav_msgs`、`piper_msgs`、`vision_msgs` 自定义字段（已随 `dridl` 拉取，待逐条展开）。
