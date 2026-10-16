# ROS2 Parameters CLI 命令快速参考

## 📋 基础命令

### 列出参数
```bash
# 列出所有参数
ros2 param list

# 列出特定节点的参数
ros2 param list /node_name
```

### 获取参数
```bash
# 获取单个参数
ros2 param get /node_name param_name

# 获取多个参数示例
ros2 param get /params_server device_name
ros2 param get /params_server update_rate
```

### 设置参数
```bash
# 设置字符串参数
ros2 param set /node_name param_name "value"

# 设置整数参数
ros2 param set /node_name param_name 42

# 设置浮点参数
ros2 param set /node_name param_name 3.14

# 设置布尔参数
ros2 param set /node_name param_name true
ros2 param set /node_name param_name false
```

## 📁 文件操作

### 加载参数文件
```bash
# 从YAML文件加载参数
ros2 param load /node_name config.yaml

# 示例
ros2 param load /params_server config/params_demo.yaml
```

### 保存参数文件
```bash
# 导出参数到YAML文件
ros2 param dump /node_name > params_export.yaml

# 示例
ros2 param dump /params_server > my_params.yaml
```

## 🚀 启动时设置参数

### 命令行设置
```bash
# 运行节点时设置参数
ros2 run package_name executable -p param_name:=value

# 设置多个参数
ros2 run params_service params_server_cpp \
  -p device_name:=my_device \
  -p update_rate:=20 \
  -p enable_debug:=true \
  -p max_distance:=75.5
```

### Launch文件设置
```python
Node(
    package='params_service',
    executable='params_server_cpp',
    parameters=[{
        'device_name': 'my_device',
        'update_rate': 20,
        'enable_debug': True,
        'max_distance': 75.5,
    }],
)
```

## 📋 参数配置文件 (YAML)

### 基本格式
```yaml
/node_name:
  ros__parameters:
    param1: value1
    param2: 42
    param3: 3.14
    param4: true
```

### 多节点配置
```yaml
/node_1:
  ros__parameters:
    device_name: "device_1"
    update_rate: 10

/node_2:
  ros__parameters:
    device_name: "device_2"
    update_rate: 20
```

## 🔍 调试和检查

### 查看参数详细信息
```bash
# 使用ros2 param list -v 查看更多信息
ros2 param list /params_server

# 逐个查看每个参数
ros2 param get /params_server device_name
ros2 param get /params_server update_rate
ros2 param get /params_server enable_debug
ros2 param get /params_server max_distance
```

### 监听参数变化事件
```bash
# 在另一个终端运行
ros2 echo /parameter_events
```

## 📝 实际应用示例

### 场景1：配置机器人设备
```bash
# 终端1: 启动参数服务器
ros2 run params_service params_server_cpp

# 终端2: 配置机器人参数
ros2 param load /params_server config/robot_config.yaml

# 终端3: 验证配置
ros2 param list /params_server
ros2 param get /params_server device_name
```

### 场景2：动态调整参数
```bash
# 启动时使用默认配置
ros2 run params_service params_server_cpp

# 运行中修改参数
ros2 param set /params_server update_rate 30
ros2 param set /params_server enable_debug true

# 保存修改后的配置
ros2 param dump /params_server > final_config.yaml
```

### 场景3：批量参数管理
```bash
# 从文件加载所有参数
ros2 param load /params_server config/params_demo.yaml

# 修改单个参数
ros2 param set /params_server device_name new_device

# 导出当前配置
ros2 param dump /params_server > current_state.yaml
```

## 💡 最佳实践

### 参数命名规范
- 使用小写字母和下划线: `device_name`, `update_rate`
- 避免特殊字符: ✓ `max_distance`, ✗ `max-distance`
- 使用有意义的名称: ✓ `enable_debug`, ✗ `flag1`

### 参数类型
| 类型 | 示例 | 说明 |
|------|------|------|
| string | "device_1" | 文本参数 |
| integer | 42 | 整数参数 |
| double | 3.14 | 浮点参数 |
| boolean | true/false | 布尔参数 |
| array | [1, 2, 3] | 数组参数 |

### 参数验证
- 在Python中使用 `add_on_set_parameters_callback()` 验证参数
- 确保参数类型和值的有效性
- 提供有用的错误消息

## 🔗 相关资源

- [ROS2 参数官方文档](https://docs.ros.org/en/humble/Concepts/Basic/About-Parameters.html)
- [ros2 param 命令](https://docs.ros.org/en/humble/How-To-Guides/Node-arguments.html)
- [参数化launch文件](https://docs.ros.org/en/humble/How-To-Guides/Overriding-Launch-Arguments.html)

## ❓ 常见问题

**Q: 如何持久化参数设置？**
A: 保存参数到YAML文件，然后在启动时加载。

**Q: 参数改变需要多长时间生效？**
A: 参数立即生效，但应用需要实现参数回调来响应变化。

**Q: 如何在节点间共享参数？**
A: 使用同一个参数命名空间和节点名称，所有参数都是全局可访问的。

**Q: 如何重置参数为默认值？**
A: 重新启动节点或手动设置为原始值。
