# 04 · 通信链路协议

四条链路：① 手柄→主控（UDP 裸帧）② App→主控（UDP/TCP JSON 帧）③ 主控↔下位机（ECAN 总线）④ 主控↔MCU（串口帧）。

---

## ① 手柄链路（Retroid / Skydroid → 主机）

来源：官方 SDK `sdk_deploy/src/M20_sdk_deploy/third_party/gamepad/`（`gamepad_keys.h`、`gamepad.cpp`、`retroid_gamepad.cpp`、`skydroid_gamepad.cpp`）。

- 传输：**UDP**，默认端口 **12121**（`kDefaultPort`）。
- 帧头：`0x55 0x66`（`kHeader`）。
- 固定结构（`#pragma pack(1)`）：

| 偏移 | 字段 | 类型 | 说明 |
| --- | --- | --- | --- |
| 0 | `stx[2]` | u8×2 | `0x55 0x66` |
| 2 | `ctrl` | u8 | 控制字节 |
| 3 | `data_len` | u16 | 数据长度 |
| 5 | `seq` | u16 | 序号 |
| 7 | `id` | u8 | 手柄类型：1=Retroid，2=Skydroid |
| 8 | `crc16` | u16 | CRC-16 校验 |
| 10 | `data[32]` | — | 16 通道 × 2 字节 |

- **Retroid 载荷**（`RetroidGamepadData.data`）：`buttons[10]`(u16) + `left_axis_x/y`(i16) + `right_axis_x/y`(i16) + `axis_buttons[2]`(u16)。摇杆范围 `kJoystickRange=1000`；按钮位含 R1/L1/start/select/R2/L2/A/B/X/Y/上左下右/左右摇杆按键。
- **Skydroid 载荷**：`right_axis_x/y`(i16) + `left_axis_y/x`(i16) + `switch_keys[4]`(u16) + `buttons[8]`(u16)。
- 解析流程：`UpdateData()` → `DataIsValid()`（CRC 校验）→ 填 `RetroidKeys/SkydroidKeys`。

## ② App / SDK 控制链路（JSON 帧）

来源：`interface/user_command/gamepad_interface.hpp`（`ParseHeader`/`AddDataHeader`/`ParseJson`）。

- 帧头 **16 字节**：

| 偏移 | 值 | 说明 |
| --- | --- | --- |
| 0 | `0xEB` | magic |
| 1 | `0x90`=内部 / `0x91`=用户 | 来源类型 |
| 2 | `0xEB` | magic |
| 3 | `0x90` | magic |
| 4-5 | `bodyLen` (LE, u16) | JSON 体长度 |
| 6-7 | `data_id` (LE, u16) | 数据 ID |
| 8 | `0x01` | dateFlag |
| 9-15 | `0x00` | 保留 |
| 16.. | JSON body | `data` |

- JSON 结构：
```json
{"PatrolDevice":{"Items":{...},"Type":<int>,"Command":<int>,"Time":"YYYY-MM-DD HH:MM:SS.mmm"}}
```
- 指令表（`mHandleMap_`）：

| Type | Command | 处理 | 说明 |
| --- | --- | --- | --- |
| 100 | 100 | `Handle_Heartbeat` | 心跳，回包 `ErrorCode=0` |
| 2 | 21 | `Handle_Steer` | `Items.X`=forward_vel_scale, `Items.Y`=side_vel_scale, `Items.Yaw`=turnning_vel_scale |
| 1101 | 12 | `Handle_Key` | `Items.KeyList` 字符串数组：`G20_KEY_L1/L2/R1/R2` |

- 按键→状态机（`Handle_Key`）：
  - `L1`：WaitingForStand/LieDown → **StandingUp**
  - `L2`：StandingUp → **RLControlMode**
  - `R1`：StandingUp/RLControlMode → **LieDown**
  - `R2`：→ **JointDamping**（任意态）
- 反馈：`buildResponse()` 回填 `Items.ErrorCode`(0 成功；1 未知命令；2 缺字段；3 类型错；4 IP 冲突) 与 `Items.ErrorMessage`。
- 防冲突：同一时刻仅允许单一控制 IP，切换 IP 需间隔 >2s，否则返回 `IP Conflict`。
- 心跳类：`interface/network/heartbeat.hpp`（`wakeUp(netInfo)`）。

## ③ 电机/关节总线（ECAN）

来源：`/opt/robot/include/ecanmaster/`（`motor.h`、`base_actor.h`、`types/data_structures.h`）+ `lib/libecanmaster.so` + `share/ecan_master/bin/ecan-master`。

- 物理：**CAN-FD 帧承载于以太网**（原始套接字 `SocketRaw` + UDP `CanFdNetBuffer` 双路径 + CRC），绑定网卡 `ecan_nic=["eth1"]`（`robot_hardware_info.toml`，实为 `rk_gmac-dwmac`，非 EtherCAT），另有串口 `ecan_uart_port=["/dev/ttyS0"]`。
- 线程：`Motor(ethname, thread_priority, cpu, SCHED_FIFO, ...)`，`kSDKRunCPUIndex=5`。
- 关节数上限 `kJointCount=32`，单通道 `kSingleJointNumMax=7`，通道上限 `kCanChannelNumMax=4`。
- 数据结构 `JointUnit`（`#pragma pack(2)`）：
```c
XYZ board_info;   // { u8 board_id; u8 can_ch; u16 can_id; }  (联合 u32 xyz)
union { JointUnitData joint_data; u8 buffer[sizeof(JointUnitData)]; };
union { u16 status_word; u16 control_word; };
u16 data_id;
```
`JointUnitData` = `{ float pos; float vel; float tor; union{int16 motor_temp|kp}; union{int16 driver_temp|kd}; }`
- 电机命令索引 `CommandIndex`：`kIndexDisable=1, kIndexEnable=2, kIndexCalibration=3, kIndexMotorControl=4, kIndexMotorReset=5, kIndexSetHome=6, kIndexSetGear=7, kIndexSetID=8, kIndexSetCanTimeout=9, kIndexSetBandwidth=10, kIndexSetLimitCurrent=11, kIndexSetUnderVoltage=12, kIndexSetOverVoltage=13, kIndexSetMotorTemperature=14, kIndexSetDriverTemperature=15, kIndexSaveConfig=16, kIndexErrorReset=17, kIndexWriteAppBackStart=18, kIndexWriteAppBack=19, kIndexCheckAppBack=20, kIndexDfuStart=21, kIndexGetVersion=22, kIndexGetStatusWord=23, kIndexGetConfig=24, kIndexOutEncoderCalibration=25, kIndexGetOutEncoder=26, kIndexCalibReport=31`
- 电池：`BatterySensorData`（256B，含 `serial_num[32]`、`cell_voltage[20]`、`ch_plus_mV`、`bat_resp_code`）。
- 固件：`share/ecan_master/bin/ecan_V2.0.15_9f08d7e5dc341ede.bin`（`ecan_version="1.1.1"`, `firmwares.this_version="1.0.0"`）。

## ④ MCU（SensorHub）串口协议

来源：`/opt/robot/include/mcu_protocolstack.h` 与 `deep_cmd.h`。

- 串口：`mcu_ProtocolStack(device="/dev/ttyS3")`（默认；`ecan_uart_port` 另指 `/dev/ttyS0`）。存在 `/dev/ttyS0,S1,S3,S5,S6,S9`。
- 帧头 `frameHeader_t`（magic `0xEE 0xEF`）：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `header[2]` | u8×2 | `0xEE 0xEF` |
| `frame_id` | u8 | 帧 ID |
| `version` | u8 | 版本 |
| `type` | u8 | 类型 |
| `func_code` | u8 | 功能码 |
| `size` | u16 | 数据长度 |
| `crc16` | u16 | 校验 |
| data | u8[] | FRAME_DATA_BIAS=10 起 |

- 功能码 `FuncCode`：`NO_RESPONSE_REQUEST=0x15`、`ACK_REQUEST=0x16`、`RESPONSE_WITH_CONTENT=0x17`、`RESPONSE_FRAME=0x21`。
- 命令 `FrameHead{size, code, state, timestamp_ns, frame_id}`；`ServiceCode`：`kCodeQueryStatus=0`、`kCodeNeckMotor=1`、`kCodeLight=2`。
- 灯效 `LightPresetMethod`（眼灯/照明/尾灯，如 `0x020001` 眼灯常亮、`0x040C03` 尾灯红常亮…）；`NeckParam.angle ∈[0,1000]`（500 居中）；`FrameBodyRespond` 含超声/颈/触摸/眼灯/尾灯/照明灯。

---

## ⑤ 链路频率/端口汇总（待运行时补测确认）

| 链路 | 物理/传输 | 端口/通道 | 频率 | 证据 |
| --- | --- | --- | --- | --- |
| 手柄→主机 | UDP | 12121 | 待测 | SDK gamepad 常量 |
| App→主机 | UDP/TCP | 待测（帧含 30001/30002 服务为另一路） | 心跳 + 事件 | `gamepad_interface.hpp` |
| 主机↔主机 | 以太网 + Fast DDS | UDP + SHM | `drdds` 话题 | `fastdds.xml` |
| 关节指令 | ECAN(EtherCAT) | eth1 | `chrt 90` 200Hz(5ms) | `rl_deploy.service`/`state_machine_base.h` |
| 点云 UDP | UDP | 30100 | 请求-响应 | `params.yaml` |
