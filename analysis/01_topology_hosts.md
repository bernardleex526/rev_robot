# 01 · 主机与网络拓扑

## 1. 主机清单（实测）

| 主机 | 主机名 | eth0 | eth1 | 其他 | eMMC | 角色（os_type） | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | `host` | 10.21.33.103 | 10.21.31.103 | eth2 10.21.31.103? → 见下、wlan0 10.21.41.1、p2p0 10.8.13.122 | mmcblk0 115.3GiB | **CA9B_AOS** | 主控/自主；Wi-Fi AP 所在；SSH 入口 |
| B | `host` | 10.21.31.104 | — | docker0 | 同上 | **CA9B_GOS** | 运行 encryption_node / uwb_node |
| C | `host` | 10.21.33.106 | 10.21.31.106 | docker0 | 同上 | **CA9B_NOS** | 导航（localization/planner/…) |

证据：`/var/opt/robot/conf/robot_hardware_info.toml` →
```
[robot] ip_subnet="10.21.31"  aos_id="103" gos_id="104" vos_id="105" nos_id="106"
```
`/opt/robot/os_type` = `CA9B_AOS`（主机 A）；`/opt/robot/version` = `103_v1.0_v2.0_0728`。
三台机器 `/etc/machine-id` 相同（金镜像未重生成），但 `/proc/device-tree/serial-number` 各不相同（a9fa1fde…/9763ef50…/819270e9…），确认为三台实体机。

## 2. 主机 A 网络接口（实测 `ip -4 addr`）

```
lo     127.0.0.1/8
eth1   10.21.32.103/24     (platform fe1b0000.ethernet)   —— 网卡自身命名与 NWC 冲突需注意
eth0   10.21.33.103/24     (platform fe1c0000.ethernet)
eth2   10.21.31.103/24     (USB 网卡 0fe6:9900 USB 10/100 LAN)
wlan0  10.21.41.1/24       (Realtek 0bda:c820 802.11ac)  —— AP，SSID=CA9B_NO.1546_24G
p2p0   10.8.13.122/23      (同上芯片，Wi-Fi Direct/数据）
docker0 172.17.0.1/16 (DOWN)
```
注意 `/var/opt/robot/conf/NWC.toml` 记录 `eth0=10.21.33.103, eth1=10.21.31.103`，与运行时实际接口编号有出入（eth1/eth2 互换）——命名依赖 USB 枚举顺序。

## 3. 内网其余设备（主机 A 网段扫描，只读）

- `10.21.33.201` / `10.21.33.202`：**Robosense Airy 激光雷达**（HTTP 标题 “Robosense Lidar”；UDP 组播 224.10.10.201/202，msop 6691/6692，difop 7781/7782，imu 6681/6682）。
- `10.21.31.104` / `10.21.31.106`：主机 B / C（SSH OpenSSH 8.2p1 Ubuntu 20.04）。
- `10.21.31.104/106 的 MAC` 为本地管理位地址（02:7A:93… / AA:2C:B2…），疑似虚拟/软 MAC。

## 4. 本机接入方式

- 目标网络：Wi-Fi `CA9B_NO.1546_24G`（5.18GHz，AP BSSID 14:0A:02:8C:3C:9C = 主机 A wlan0）。
- 本机 `wlp4s0` 获址 `10.21.41.145/24`，网关 10.21.41.1（= 主机 A）。
- 本机已存在经主机 A 转发到 `10.21.31.0/24` 的静态路由（主机 A `ip_forward=1`），据此可直达主机 B/C。
- SSH：`user@10.21.41.1`（密钥已互信；口令为单引号 `'`）。辅助脚本：`dog.sh` / `dogsudo.sh` / `rsudo.sh`。

## 5. 时间同步与实时性

- `ptp4l.service` + `phc2sys.service` 运行（IEEE 1588 PTP），并有 `ptp103.sh/ptp104.sh/ptp106.sh` 按主机启动（`scripts/board_resources/wifi/`）。
- 启动等待脚本 `wait_net.sh` 会阻塞直到 PTP 同步（`date` 年份 > 2024）才继续启动业务，说明时间同步是系统级硬前提。
- 实时性：`rl_deploy` → `chrt 90 taskset -c 4,5`；`lio_ddsnode` → `chrt 35 taskset -c 5,6,7`；`cpu_node` → `taskset -c 1,2,3`。8 核分工明显（0 核留给系统/中断，`ca9b-eth0-irq-affinity.service` 做网卡 IRQ 亲和）。

## 6. 磁盘布局（三台一致）

```
mmcblk0 115.3G
 p1 8M p2 4M p3 256M /boot p4 128M p5 32M
 p6  100M  /var/opt/robot/conf      (ext4)
 p7  7.8G  /var/opt/robot/log       (ext4)
 p8    2G  /var/log                 (ext4)
 p9  7.8G  /opt/robot               (ext4)
 p10 7.8G  /var/opt/robot/record    (ext4)
 p11 62.5G /var/opt/robot/data      (ext4)   # 地图/录包
 p12 8.5G  /root-ro                 (ext4)   # 只读根 lower
 p13 18.4G /userdata                (ext4)   # 可写 upper
```
根文件系统为 overlayroot（`/` = overlay，`/root-ro` 只读）：对狗的任何误写默认落到 `/userdata`，系统盘不可变，天然降低变砖风险。
