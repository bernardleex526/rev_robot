# 02 · 软件模块、进程与服务

## 1. `/opt/robot` 目录（主机 A，274MB / 10396 文件）

```
/opt/robot
├── bin/         顶层工具（见 §4）
├── include/     ★协议头：deep_cmd.h, mcu_protocolstack.h, mcu_control.h, mcu_agent.hpp,
│                SerialPort.hpp, common_lib.h, ecanmaster/{motor.h,base_actor.h,robot_hwi.hpp,types/data_structures.h}
├── lib/         libfastrtps.so.2.14 / libfastcdr / libfoonathan_memory / liblog4cplus / libopencv* /
│                libecanmaster.so / libsensorhub_shared.so / librte-checker.so / libtinyxml2
├── share/       ★功能模块（见 §2）
├── scripts/     启动、Wi-Fi、RTSP、存储清理、固件升级
├── etc/ samples/ tests/ tools/ docs/
├── fastdds.xml  Fast DDS 传输配置
├── os_type      CA9B_AOS
└── version      103_v1.0_v2.0_0728
```

## 2. `share/` 功能模块（8 个）

| 模块 | 二进制 | 作用（证据） |
| --- | --- | --- |
| `basic_server` | basic_server (3.2MB) | 运动/导航服务端 + 速度档位配置；监听 30001/30002；`conf/basic_server.toml`、`conf/authority_code.toml` |
| `rl_deploy` | rl_deploy (94MB, 内嵌 onnxruntime) | RL 策略推理与关节指令下发；`lib/onnxruntime/libonnxruntime.so.1.20.0` |
| `lio-perception` | lio_ddsnode / lio_command | 激光-惯性里程计 + 深度图/高程图；FAST-LIO 系头文件（`include/dr_lio/*`） |
| `height_map_nav` | height_map_nav (1.5MB) | 2.5D 高程图导航/落足；`config/height_map_dds.yaml`、`height_map_ros.yaml` |
| `node_driver` | cpu_node, ctrlmcu_node, gps_node, yesense_node, uwb_node, encryption_node, system_status_node, rslidar, hsLidar | 传感器/下位机驱动集合（每个配 `config/*.yaml`） |
| `ecan_master` | ecan-master + `ecan_V2.0.15_9f08d7e5dc341ede.bin` | EtherCAT 类电机总线主站 + 固件 |
| `mcu_update` | `CA9B_f1_app_v2.1.0.bin` | STM32(F1) 下位机固件包 |
| `rte_checker` | run | 实时性能/资源检查（配 `rte_checker.service`） |

## 3. systemd 服务与启动顺序

`scripts/board_resources/start_ctrl/start_ctrl.sh` 依据 `os_type` 分流：

**AOS（103）**：`wait_net(eth0 eth1 eth2, ping .106 + .104) → performance → ctrlmcu → gps_node → cpunode → yesense → rl_deploy → basic_server → height_map_nav → lio-perception →(5s) rob_bag →(5s) rsdriver → hsLidar`

**GOS（104）**：`wait_net(eth0) → performance → encryption_node → cpunode → uwb_node → rsdriver → hsLidar`

**NOS（106）**：`wait_net(eth0 eth1, ping .103) → performance → cpunode → yesense → charge_manager → reflective_column → handler → localization → passable_area → global_planner → planner → rsdriver → hsLidar`

顶层 `/opt/robot/scripts/start.sh`（`start.service`）：`ldconfig.sh` → `wifi/host_start.sh`（起 AP）→ `rtsp_service/start_server.sh`（mediamtx 视频）→ 磁盘日志清理循环。

主机 A 实测运行中服务（45 个）：`basic_server, cpunode, ctrlmcu, gps_node, height_map_nav, hsLidar, lio-perception, rl_deploy, rob_bag, rsdriver, rte_checker, yesense, start, dr_wifi, firmware_upgrade, performance, storage_check, dpkg_ln, resize, ptp4l, phc2sys, snmpd, vsftpd, tftpd-hpa, docker, containerd, chrony, avahi, bluetooth, cups, …`

## 4. `/opt/robot/bin` 顶层工具

| 文件 | 推断用途 |
| --- | --- |
| `mcu_control` (1.8MB) / `mcu_test` / `mcu_update` (2.1MB) | 下位机控制/测试/升级 |
| `FirmwareAssistant` / `DriverOTA` / `BatteryOTA` | 固件助手、驱动器 OTA、电池 OTA |
| `SetHome` / `AutoSetHome` / `AutoSetHome2` / `CR1BSethome` | 关节零位标定 |
| `airy` / `airy_pwm_calib201` / `airy_pwm_calib202` | Airy 雷达 PWM 标定（201/202 对应两颗雷达） |
| `G20Manul` | 手柄手动控制（G20 遥控器） |
| `export_img` | 镜像导出 |
| `proc_checker` | 进程守护检查 |

## 5. `scripts/` 关键脚本

- `board_resources/wifi/host_start.sh`, `ap_start.sh`, `loop_start_ap.sh`, `wifi_ctl.sh`, `80-net-rename.rules`, `rules.v4`（iptables）, `password`（★凭据文件，应隔离）
- `board_resources/rtsp_service/`：`mediamtx`（27MB）+ `mediamtx.yml` + `push_video.sh` + OpenCV 运行库 + `SM_USB_107X_*.json`（摄像头参数）
- `board_resources/storage_space/delete_log_*.sh`：按 300s 周期清理日志/录像
- `board_resources/start_ctrl/`：见 §3
- `system/ldconfig.sh`、`system/config.yaml`、`system/.robots`（2.3MB，疑设备清单）
- `setup_ros2.sh`：按 eth0 末段（103/106/104）把本机 IP 注入 `fastdds.xml` 的 `interfaceWhiteList`，并 source ROS2 环境

## 6. 权限与运行身份

- 业务进程以 root 运行（systemd）或经 `sudo` 启动；`user`（uid 1003，groups: adm,sudo）。
- `run.sh` 里 `ulimit -c unlimited` 并写 `/proc/sys/kernel/core_pattern=/var/opt/robot/log/system/coredump.%e.%p.%t`（崩溃转储保留，可作为反推运行时行为的证据来源）。
