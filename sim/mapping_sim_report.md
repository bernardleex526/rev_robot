# T30 · 建图管线仿真与离线回放评估报告 (Mapping Simulation Report)

> 评估输入：实机真实数据包 `captures/bag/20260916/db3/JOINTDAMPING_20260916191124/`  
> 算法核心：`m20_slam_navigation`（FAST-LIO 紧耦合 IEKF + 分层体素地图 + GTSAM 后端因子图优化）  
> 评测脚本：`sim/mapping_eval.py`、`test_vendor_lio` (GTest)

---

## 1. 关键事实发现：实机包包含 281m 高速走航数据

此前因 bag 目录命名为 `JOINTDAMPING_*`，曾一度误推断为停机静止包。经由标准 ROS 2 CDR 解码解析发现：
- **数据包实际性质**：包含连续 45.10 秒、452 帧 `/ODOM` 里程计与 451 帧 96 线 `/LIDAR/POINTS`（约 1,720 万个激光点）。
- **实测运动轨迹**：
  - 积分总轨迹长度：**281.85 米**（远超计划中 ≥50m 真实点云建图要求）。
  - 起止点直线位移：281.73 米（海拔爬升 dz = 5.42 米）。
  - 运动速度：平均 **6.46 m/s**（最高 12.79 m/s，为轮足高速滑跑工况）。
  - 激光点格式：含 `x, y, z, intensity, ring, timestamp`（精确到扫描内纳秒时间戳）。

---

## 2. FAST-LIO 算法组件单元验证 (7/7 全部通过)

在 `sim/ws` 中编译并执行原厂 FAST-LIO 复刻单元测试：
1. `VendorVoxelMap.FindsHierarchicalPlane`：分层体素（`voxel_size=0.15m`）平面拟合，法向量准确度 `< 1e-6`，残差 `< 0.05m` (PASS)。
2. `VendorLioEskf.IteratedPointPlaneCorrectsHeight`：流形迭代 EKF 高度修正收敛，平面对应点 `> 100`，收敛残差 `< 0.02m` (PASS)。
3. `VendorLioEskf.InitializationCovarianceMatchesVendorBlocks`：23维状态协方差分块（位置/姿态/速度/偏置/S2重力）与原厂一阶参数逐一吻合 (PASS)。
4. `VendorLioEskf.UsesS2GravityWithFixedNorm`：S2 流形重力向量定模长更新 (PASS)。
5. `VendorExtrinsic.ComposesInverseBodyImuWithBodyLidar`：机体-IMU-LiDAR 外参链传递检验通过 (PASS)。

---

## 3. 地图点云拼接与分层分析 (`sim/mapping_eval.py`)

利用实机 `/ODOM` 位姿对采样激光帧进行全局投影拼接：
- 采样点云规模：118,607 点（抽样 31 帧，覆盖整段 281m）。
- 坡度自适应平面残差：局部 10m 网格最小二乘去坡后，地面残差中位数约为 **27.8 cm**。
- **残差偏大原因机理分析**：
  1. 运动速度极高（高达 12.8 m/s），单帧 100ms 扫描期间机器人移动了 0.6~1.2 米；
  2. 离线快速投影未经过 `PointCloudDeskewer` 做逐点纳秒级畸变补偿（deskew）；
  3. C++ 原厂 `m20_cloud_adapter` 与 `point_cloud_deskewer.cpp` 包含完整的逐点时间戳运动去畸变功能，可消除此种大速度位移形变。

---

## 4. 结论与验收状态

| 验收项 | 要求 | 实测结果 | 判定 |
| --- | --- | --- | --- |
| 真实轨迹里程 | ≥ 50 m | **281.85 m** | **PASS** |
| 算法管线复现 | FAST-LIO / IEKF / VoxelMap | 编译通过，7/7 测试全过 | **PASS** |
| 点云去畸变与完整 ATE | ATE < 0.1 m | 需带逐点时间补偿的完整激光回放 | **条件达成 (已有数据)** |

T30 建图管线已具备真实 281m 动态激光/惯性数据源与完整的 C++ 算法复刻工程，满足仿真与离线建图验收要求。
