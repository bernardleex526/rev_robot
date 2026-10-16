# ROS2 Parameters Service 示例

这个示例展示如何在ROS2中使用参数服务，并通过CLI工具进行参数配置和获取。

## 功能特性

- ✅ 声明和管理多种类型的参数（string, int, bool, double）
- ✅ 实时监听参数变化事件
- ✅ 定期显示当前参数值
- ✅ 支持YAML文件批量加载参数
- ✅ 提供C++和Python两种实现
- ✅ 完整的CLI命令示例

## 参数类型

本示例声明以下参数：

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `device_name` | string | `default_device` | 设备名称 |
| `update_rate` | int | `10` | 更新频率(Hz) |
| `enable_debug` | bool | `false` | 是否启用调试 |
| `max_distance` | double | `100.0` | 最大距离(m) |

## 编译

```bash
cd ~/code/code/ysc_job/drdds-ros2-msgs/example
colcon build --packages-select params_service
source install/setup.bash
```

## 使用方法

### 方式1：运行C++ 参数服务器

```bash
ros2 run params_service params_server_cpp
```

### 方式2：运行Python 参数服务器

```bash
ros2 run params_service params_server.py
```

### 方式3：使用Launch文件启动

```bash
ros2 launch params_service params_demo.launch.py
```

## CLI 命令示例

### 1. 列出所有参数

```bash
# 列出所有节点和参数
ros2 param list

# 列出特定节点的参数
ros2 param list /params_server
```

**输出示例：**
```
/params_server:
  device_name
  enable_debug
  max_distance
  update_rate
```

### 2. 获取参数值

```bash
# 获取字符串参数
ros2 param get /params_server device_name

# 获取整数参数
ros2 param get /params_server update_rate

# 获取布尔参数
ros2 param get /params_server enable_debug

# 获取浮点参数
ros2 param get /params_server max_distance
```

**输出示例：**
```
String value is: default_device
Integer value is: 10
Boolean value is: False
Double value is: 100.0
```

### 3. 设置参数值

```bash
# 设置字符串参数
ros2 param set /params_server device_name my_device

# 设置整数参数
ros2 param set /params_server update_rate 20

# 设置布尔参数
ros2 param set /params_server enable_debug true

# 设置浮点参数
ros2 param set /params_server max_distance 50.5
```

**输出示例：**
```
Set parameter successful
```

### 4. 从YAML文件加载参数

```bash
# 使用绝对路径加载配置文件
ros2 param load /params_server /home/feng/code/code/ysc_job/drdds-ros2-msgs/example/src/params_service/config/params_demo.yaml

# 或使用相对路径（需要在项目根目录）
cd /home/feng/code/code/ysc_job/drdds-ros2-msgs/example/src/params_service
ros2 param load /params_server config/params_demo.yaml

# 或使用install目录中的配置
ros2 param load /params_server /home/feng/code/code/ysc_job/drdds-ros2-msgs/example/install/params_service/share/params_service/config/params_demo.yaml
```

### 5. 将参数保存到YAML文件

```bash
# 导出当前参数到YAML文件
ros2 param dump /params_server > my_params.yaml

# 查看导出的文件
cat my_params.yaml
```

**输出示例：**
```yaml
/params_server:
  device_name: demo_device
  enable_debug: false
  max_distance: 150.0
  update_rate: 20
```

### 6. 参数删除（重置为声明的默认值）

```bash
# ROS2当前版本不直接支持删除，但可以重新设置为默认值
ros2 param set /params_server device_name default_device
```

## 参数配置文件 (YAML)

编辑 `config/params_demo.yaml` 文件配置初始参数：

```yaml
params_server:
  ros__parameters:
    device_name: "demo_device"
    update_rate: 20
    enable_debug: false
    max_distance: 150.0
```

在launch文件中使用此配置：

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='params_service',
            executable='params_server_cpp',
            name='params_server',
            parameters=['config/params_demo.yaml'],
            output='screen',
        ),
    ])
```

## 监听参数变化

本示例会自动监听参数变化并输出日志：

```
[INFO] [1234567890.123456789] [params_server]: --- Parameters Changed ---
[INFO] [1234567890.234567890] [params_server]: Parameter 'device_name' changed
[INFO] [1234567890.345678901] [params_server]: New value: new_device
```

## Python客户端示例

使用 `params_client.py` 以编程方式获取和设置参数：

```bash
ros2 run params_service params_client.py
```

## 常见问题

### Q1: 如何在节点启动时传递参数？

```bash
ros2 run params_service params_server_cpp -p device_name:=my_device -p update_rate:=30
```

### Q2: 如何在Launch文件中设置参数？

```python
Node(
    package='params_service',
    executable='params_server_cpp',
    name='params_server',
    parameters=[{
        'device_name': 'my_device',
        'update_rate': 30,
        'enable_debug': True,
        'max_distance': 75.5,
    }],
    output='screen',
)
```

### Q3: 如何使用参数进行动态重配置？

1. 在C++/Python代码中使用参数回调
2. 监听参数事件并做出相应的动作
3. 示例中已包含参数变化回调功能

### Q4: 如何在ROS节点中访问参数？

**C++:**
```cpp
this->get_parameter("device_name", device_name_value);
auto value = this->get_parameter("update_rate").as_int();
```

**Python:**
```python
value = self.get_parameter('device_name').value
value = self.get_parameter('update_rate').value
```

## 相关文档

- [ROS2 官方参数文档](https://docs.ros.org/en/humble/Concepts/Basic/About-Parameters.html)
- [ros2 param 命令参考](https://docs.ros.org/en/humble/How-To-Guides/Node-arguments.html)

## 许可证

Apache License 2.0
