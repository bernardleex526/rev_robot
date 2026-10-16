# 09 · 硬件与外设

## 1. 计算与存储

- 3× aarch64 主机，CPU `part 0xd05` = **ARM Cortex-A55**，`/proc/cpuinfo` 8 核（`nproc` 在 SSH 会话下显示 4，疑受 cpuset/亲和影响）；内存 16GB（`Mem: 15Gi`）。
- 存储：**eMMC `mmcblk0` 115.3 GiB**（13 分区，见 01 节）+ `mmcblk0boot0/1`（各 4MB，eMMC boot 区）。
- 网络：千兆以太网 ×2（SoC MAC `fe1b0000/fe1c0000`）、USB 10/100 网卡（0fe6:9900）、USB 802.11ac（Realtek 0bda:c820）。

## 2. 传感器

| 传感器 | 型号/接口 | 连接 | 驱动 | 话题 |
| --- | --- | --- | --- | --- |
| 激光雷达 ×2 | **Robosense Airy**（RSAIRY） | 以太网 UDP 组播 224.10.10.201/202，msop 6691/6692，difop 7781/7782，imu 6681/6682 | `rslidar`（+冗余 `hsLidar`） | `/LIDAR/POINTS`, `/LIDAR/POINTS2`, `/LIDAR/IMU201/202`, `/LIDAR/STATUS` |
| IMU | **Yesense** | `/dev/ttyS9` @115200 | `yesense_node` | `/IMU_YESENSE`, `/IMU` |
| GNSS/RTK | **Fibocom** 模组 | 内部 | `gps_node` | `/GPS`, `/FIBOCOM/net_rtk/gngga`, `/FIBOCOM/net_rtk/heading`, `/fibo_fusion_pose` |
| UWB | 模块 | 串口 | `uwb_node`（GOS） | `/UWB_ENABLE`, `/UWB_ONLINE`, `/UWB_ODOM_LOST` |
| 摄像头 ×2（广角） | USB UVC | `/dev/video0`, `/dev/video2`（**当前未枚举**） | gstreamer + mediamtx | RTSP `rtsp://<ip>:8554/video1`, `video2` |
| 超声/触摸/颈 | SensorHub MCU | 串口 | `mcu_control`/`ctrlmcu_node` | 见 MCU 协议（04 节） |
| 灯效 | 眼灯/照明/尾灯 | MCU | — | `/LED/STATUS`, `/LED/*` 服务 |

## 3. 总线

- **ECAN（CAN-FD over Ethernet，非 EtherCAT）**：`libecanmaster.so` **在 `rl_deploy` 进程内**（无独立 `ecan-master` 进程），符号含 `SocketRaw::Send`/`UdpSocket::updateSingleData(CanFdNetBuffer&)`/`CalCRCEPht`/`JointUnit[32]`，绑 `eth1`（标准 `rk_gmac-dwmac`）；电机驱动节点 `ctrlmcu_node`；固件 `ecan_V2.0.15_9f08d7e5dc341ede.bin`（实机日志确证 `ECAN Program Version 3.1.6`）。
- **MCU 串口**：`/dev/ttyS0,S1,S3,S5,S6,S9`；MCU 协议栈默认 `/dev/ttyS3`，`robot_hardware_info.toml` 指 `/dev/ttyS0` 为 ecan 串口。
- **无原生 CAN 节点**（`/dev/can*` 不存在）；总线类型 = EtherCAT-over-Ethernet + 串口，**非** SocketCAN。
- SPI/I2C：`/dev/i2c-0,3,6,9`（SPI 未见）。
- PTP：`ptp4l`/`phc2sys`（106 另有 `ptp4l/eth1`、`phc2sys/eth1`），为雷达/关节时间同步提供基准。

## 4. 执行器

- 预期 **16 自由度**：每腿 3 关节（hipx/hipy/knee）+ 1 轮毂 = 4×4。
- 关节顺序（URDF/robot 顺序）：`fl_hipx, fl_hipy, fl_knee, fl_wheel, fr_..., hl_..., hr_...`。
- MCU 侧 `JointData_dds{pos, vel, tor, kp, kd, motor_temperature, driver_temperature, status_word, control_word, data_id}`。
- 关节限位（SDK `m20_control_parameters.cpp`）：前左 `lower=[-0.4363,-2.443,-2.758] rad`、`upper=[0.6109,2.443,2.758] rad`；速限 `[45,22.4,22.4]`；力矩限 `[32.4,76.4,76.4] N·m`；轮速限 100。
- 机构尺寸：`body_len_x=0.619, body_len_y=0.130, hip_len=0.104, thigh_len=0.25, shank_len=0.25, wheel_link_len=0.040575`；`pre_height=0.12, stand_height=0.38`。

## 5. 电源

- **72V 热插拔电池**；`BatteryInfo_dds`（电压 10mV、电流 10mA、剩余/标称容量 10mAh、循环、温度×4、串数、MOS 状态）。
- 电池固件升级 `BatteryOTA`；`BATTERY_CHARGE_ENABLE` / `CHARGE_CMD` / `CHARGE_STATUS` 话题；`charge_manager`(NOS) + `reflective_column`(反光柱充电对接)。
- `basic_server.toml`：`PowerManagement.Sleep={time=5,auto=true}`、`Battery={sigleBatteryMode=true}`。

## 6. 固件与升级资产（详见 10 节）

- MCU：`share/mcu_update/bin/CA9B_f1_app_v2.1.0.bin`（STM32**F1** app）。
- ECAN：`share/ecan_master/bin/ecan_V2.0.15_9f08d7e5dc341ede.bin`。
- 顶层：`bin/FirmwareAssistant`, `bin/DriverOTA`, `bin/BatteryOTA`, `scripts/firmware_upgrade.sh`。
- 硬件版本：`BOM_version=CA9B_BOM_P1.0_v1.2`、`board_version=PCB-Y25-045_MB_CA9B_V2.0`、`motor_driver hardware/software=3.1.0`、`firmwares.this_version=1.0.0`、`ecan_version=1.1.1`。

## 7. 未知项

- 主控 SoC 具体型号（仅 `CPU part 0xd05` 可判为 A55；未取 `/proc/device-tree/compatible`）。
- 摄像头为何未枚举（可能需 `usb_ctl.sh enable` 或未接入）。
- 电池与 MCU 的确切型号/单板。
