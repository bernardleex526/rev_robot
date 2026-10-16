# 07 · 建图 / SLAM 还原（T25）

## 1. 算法判定：FAST-LIO 系（LiDAR-Inertial Odometry，紧耦合 IEKF on manifold）

证据（`/opt/robot/share/lio-perception/include/dr_lio/`）：
```
common_lib.h     use-ikfom.h     imu_processing.h     lio.h     so3_math.h
```
这 5 个头文件是 **FAST-LIO / FAST-LIO2 的原始源码文件名**：
- `use-ikfom.h` → IKFoM（Iterated Kalman Filter on Manifold，流形上的迭代 EKF）。
- `so3_math.h` → SO(3) 李群运算（EXP/LOG/右雅可比）。
- `imu_processing.h` → IMU 预积分与去畸变。
- `common_lib.h` → 体素/点云工具（本机同时存在于 `/opt/robot/include/common_lib.h`）。

结论：**LIO 前端为 FAST-LIO 家族的迭代 EKF（IEKF）紧耦合**，非 LIO-SAM/LOAM 的扫描匹配+因子图。后端回环/位姿图由 NOS 侧 `localization`（另有 NDT 重定位，见 08）。

## 2. 参数（`share/lio-perception/conf/params.yaml`）

| 参数 | 值 | 含义 |
| --- | --- | --- |
| `input_lidar_topic` | `/LIDAR/POINTS` | 雷达（drdds/速腾）|
| `input_imu_topic` | `/IMU_YESENSE` | IMU |
| `output_odom_topic` | `/LIO_ODOM` | 里程计 |
| `output_odom_topic_high_frequency` | `/LIO_ODOM_HIGH_FREQUENCY` | 高频里程计 |
| `output_aligned_cloud_topic` | `/LIO_ALIGNED_POINTS` | 里程计系累积点云 |
| `output_voxel_cloud_topic` | `/DEPTH_POINTS` | 调试点云 |
| `output_depth_image_topic` | `/DEPTH_IMAGE` | 深度图 |
| `output_accumulated_map_cloud_topic` | `/ACCUMULATED_POINTS_MAP` | 累积地图点云 |
| `lidar_type` | 1 | 0=Livox，**1=速腾(Robosense)** |
| `acc_cov` / `gyr_cov` | 0.8 / 0.8 | IMU 噪声 |
| `b_acc_cov` / `b_gyr_cov` | 0.01 / 0.01 | 偏置随机游走 |
| `extrinsic_est_en` | false | **关闭在线外参估计** |
| `extrinsic_B_I` / `extrinsic_B_L` | 4×4 单位阵 | 当前文件中 IMU/LiDAR 相对机体系外参为**单位阵（占位）** |
| `max_iteration` | 3 | IEKF 迭代次数 |
| `enable_downsample` | true, `leaf_size` 0.15；`leaf_size_body` 0.05 | 体素降采样 |
| `skip_num` | 9 | 跳点 |
| `esti_plane_threshold` | 0.1 | 平面拟合阈值 |
| `init_time` | 0.1 | 初始化时长 |
| `lidar_cov` | 0.001 | 雷达观测噪声 |
| `deepest_level/plane_level/top_level` | 2/2/1 | 多分辨率体素层级 |
| `save_full_pcd` / `full_map_save_path` | false / `/var/opt/robot/data/maps/active/full_cloud.pcd` | 全图保存开关与路径 |
| `accumulated_points.udp_output` | enable, res 0.2, **port 30100** | 累积点云 UDP 请求-响应接口 |

其余：`voxel_map.ray_casting`(level 2, range 3.0, dis_th 0.02)、`depth_image`(level 4, 20Hz, max_depth 3.0, 角分辨率 4°, body_height 0.4)、`height_map`(level 4, 20Hz, res 0.04, 100×100, z∈[-1,1])。

## 3. 传感器与安装外参

`share/node_driver/config/config.yaml`（`rslidar` 驱动）：
- 两颗 **Robosense Airy**：`lidar_type: RSAIRY`，组播 `224.10.10.201`(msop 6691/difop 7781/imu 6681) 与 `224.10.10.202`(6692/7782/6682)。
- 安装外参：前雷达 `x=+0.32028, y=0, z=-0.013, roll=0, pitch=-1.57079, yaw=-3.14159`；后雷达 `x=-0.32028, y=0, z=-0.013, roll=0, pitch=-1.57079, yaw=0`。
- `max_distance: 60`，`dense_points: true`，`use_lidar_clock: true`，`dds_frame_id: lidar_link`。

`share/node_driver/config/hsLidar.yaml`（`hsLidar` 驱动，Hesai 栈）指向同一对设备 IP `10.21.33.201/202`（udp 2361/2362，ptc 9347），外参 `x=±0.360, z=-0.013, roll=-1.5707, yaw=∓1.5707`。
→ 两个驱动监听同一物理雷达，属**冗余/过渡**实现；实际生效者需运行时确认（未决项）。

IMU：`yesense.yaml` → `/dev/ttyS9` @115200，frame `basic_id`。

## 4. 数据流（反向追踪）

```
Robosense Airy ×2 --UDP/Ethernet--> rslidar/hsLidar --> /LIDAR/POINTS(+IMU201/202)
Yesense IMU --/dev/ttyS9--> yesense_node --> /IMU_YESENSE
/LIDAR/POINTS + /IMU_YESENSE --FAST-LIO(IEKF)--> /LIO_ODOM (+HIGH_FREQUENCY) / /LIO_ALIGNED_POINTS
/LIO_ODOM + /CLOUD_REGISTERED_BODY --voxel/ray-cast--> /DEPTH_POINTS /DEPTH_IMAGE /ACCUMULATED_POINTS_MAP /height_map
                                       --(-->) 2.5D 高程图 --> height_map_nav (导航落足/避障)
```

## 5. 地图格式与产物

- 累积点云另存 `full_cloud.pcd`（**PCD**，PCL 点云格式）。
- 导航侧高程图/栅格：`height_map_nav` 输出 `/height_map`(PointCloud2)、`/HEIGHT_IMAGE`(Image)、`/grid_map`(grid_map_msgs/GridMap)、`/GRID_MAP`(OccupancyGrid)。
- 机上 `rob_bag` 每 5s 清理策略保留最近若干天，现存 **12GB** 压缩包（`/var/opt/robot/data/rob_bag/*.tar.bz2`，最大 4.26GB / 20260814）——**可直接用作 T19/T25 的运行时真值数据**，无需重新采集。

## 6. 未知项 / 待验证

- ~~`extrinsic_B_I/B_L` 在配置中为单位阵 → 真实外参可能硬编码于二进制，或在别处（`/var/opt/robot/conf`）覆盖~~ → **已确证（T33）**：二进制硬编码加载该 `params.yaml`，外参由 `YAML::convert<std::vector<double>>` 直读、长度不足即抛异常（无兜底常量），**即 identity，无覆盖**。物理雷达安装由 `rslidar` 驱动承担（`x=±0.32028`，前后合并输出到机身帧）。见 `24_obs_layout_extrinsic.md`。
- `lio_ddsnode` 已剥离符号；其与开源 FAST-LIO 的差异（自定义：深度图补坑、环视点云 UDP、高频里程计、多分辨率高度图）需 Ghidra 交叉验证。
- 双雷达融合方式（是否合并点云后统一 IEKF，还是主从）未确认。
- ATE 验证需 `T19`/rob_bag 数据 + 复现管线（M4）。
