# 10 · 资产清单（URDF/Mesh/ONNX/固件/APK/源码）

## 1. 机器人模型

| 资产 | 路径 | 说明 |
| --- | --- | --- |
| MJCF 模型 | `dump/hostA/home_user/sdk_deploy/src/M20_sdk_deploy/M20_description/m20_mjcf/mjcf/{M20.xml, scene.xml, M20_stair.xml, stair.xml}` | MuJoCo 模型（含台阶场景），可直接作 T28 数字孪生起点 |
| Mesh | 同目录 `meshes/*.stl` | **2202 个 STL** |
| URDF/Xacro | **未发现** | 仅 MJCF；URDF 需由 MJCF 转换或自建 |
| 关节顺序/限位 | `state_machine/parameters/m20_control_parameters.cpp` | 见 09 节 |

## 2. 神经网络资产

| 资产 | 路径 | 说明 |
| --- | --- | --- |
| 官方 SDK 策略 | `.../M20_sdk_deploy/policy/policy.onnx` (785KB) | MLP `obs[1,57]→actions[1,16]`，Gemm/Elu，PyTorch 2.7.0 |
| **部署策略 15 个** | `bin/policies/*.onnx`（从 `rl_deploy` 提取） | 详见 12 节；`state[1,318..366]`/时序 `[1,36,53]`；附 `bin/policies/policies_report.json` |
| ONNX Runtime | `.../third_party/onnxruntime/{arm,x86}/lib/libonnxruntime.so.1.22.0` + `share/rl_deploy/lib/onnxruntime/libonnxruntime.so.1.20.0` | 推理运行库 |
| 导出脚本 | `.../M20_sdk_deploy/scripts/pt_to_onnx.py` | `.pt → .onnx` |

## 3. 固件

| 资产 | 路径 | 说明 |
| --- | --- | --- |
| MCU app | `dump/hostA/opt_robot/share/mcu_update/bin/CA9B_f1_app_v2.1.0.bin` | STM32F1 应用 |
| ECAN 主站固件 | `dump/hostA/opt_robot/share/ecan_master/bin/ecan_V2.0.15_9f08d7e5dc341ede.bin` | 版本 2.0.15 |
| 机上副本 | `/home/user/ca9becanv2_0_3.bin` (272,908B), `/home/user/FirmwareAssistant` | — |

## 4. 应用与 SDK

| 资产 | 路径 | 说明 |
| --- | --- | --- |
| Android 控制 App | `sdk/controlapp.apk` (21.8MB) | **Flutter**，包名 `com.example.control_app` v1.0.0，label 云深处科技，minSdk 19/target 33，仅 INTERNET 权限；1807 类/100 资源；REA(JADX) 分析见 `sdk/apk_package.json` |
| 官方 SDK 源码 | `dump/hostA/home_user/sdk_deploy/src/M20_sdk_deploy/` | 含 FSM、RL 胶水、手柄协议、MJCF、DDS 接口、`samples/drdds-ros2/` |
| 手柄库 | `.../third_party/gamepad/{src,include,example}` | Retroid/Skydroid 协议 + `controlapp.apk` + fmt |
| 参考重构工程 | `dump/hostA/home_user/m20_orignal/src/m20_slam_navigation/` | 用户侧 SLAM/导航重构源码（非官方） |

## 5. 运行时数据（机上，待按需拉取）

| 资产 | 路径 | 说明 |
| --- | --- | --- |
| ROS bag 录包 | `/var/opt/robot/data/rob_bag/*.tar.bz2`（**12GB**，最大 4.26GB/20260814） | 可用于 T19/T24/T25 的运行时真值 |
| 地图目录 | `/var/opt/robot/data/maps/active/`（当前为空） | `full_cloud.pcd` 保存目标 |
| 日志 | `/var/opt/robot/log/`（3.9GB）、`/var/log`（211MB） | 含 2024/2026 多日 |
| `.debs` 包 | `/home/user/CA9B_{103,104,106}.debs`（101/46/87MB） | 各主机软件包，可离线解包复核 |

## 6. 本地产物（`/home/lee/rea`）

```
L1_knowledge_base.md            总索引
analysis/00..12_*.md            模块分析文档
dump/hostA/opt_robot/           /opt/robot 全量（274MB）
dump/hostA/home_user/           SDK + m20_orignal 源码
runtime/host*_*.txt             勘测原始输出（lsblk/服务/设备/DDS）
bin/rl_deploy, bin/basic_server 反编译对象（含 sha256）
bin/policies/*.onnx             提取的 15 个部署策略
bin/*_symbols.txt, *_layout.json REA/本地符号与布局产物
sdk/controlapp.apk, apk_package.json  APK 与 REA 分析
tools/{carve_onnx.py,extract_policies.py}  提取脚本
env.sh, dog.sh, dogsudo.sh, rsudo.sh, image_host.sh, run_images.sh  工具链
images/imaging.log              分块镜像进度
（镜像本体在 /media/lee/数据/rea_images/）
```
