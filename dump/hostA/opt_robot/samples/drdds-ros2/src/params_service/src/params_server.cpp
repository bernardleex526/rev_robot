#include "rcl_interfaces/msg/parameter_event.hpp"
#include "rcl_interfaces/srv/get_parameters.hpp"
#include "rcl_interfaces/srv/list_parameters.hpp"
#include "rcl_interfaces/srv/set_parameters.hpp"
#include "rclcpp/rclcpp.hpp"

class ParamsServer : public rclcpp::Node {
 public:
  ParamsServer() : Node("params_server") {
    // 声明参数
    this->declare_parameter("device_name", "default_device");
    this->declare_parameter("update_rate", 10);
    this->declare_parameter("enable_debug", false);
    this->declare_parameter("max_distance", 100.0);

    RCLCPP_INFO(this->get_logger(), "===== ROS2 Parameters Server =====");
    RCLCPP_INFO(this->get_logger(), "Parameters Server started successfully!");
    RCLCPP_INFO(this->get_logger(), "\n--- Declared Parameters ---");
    RCLCPP_INFO(this->get_logger(), "  device_name: %s",
                this->get_parameter("device_name").as_string().c_str());
    RCLCPP_INFO(
        this->get_logger(), "  update_rate: %lld",
        static_cast<long long>(this->get_parameter("update_rate").as_int()));
    RCLCPP_INFO(
        this->get_logger(), "  enable_debug: %s",
        this->get_parameter("enable_debug").as_bool() ? "true" : "false");
    {
      auto p = this->get_parameter("max_distance");
      double max_distance_value = 0.0;
      switch (p.get_type()) {
        case rcl_interfaces::msg::ParameterType::PARAMETER_DOUBLE:
          max_distance_value = p.as_double();
          break;
        case rcl_interfaces::msg::ParameterType::PARAMETER_INTEGER:
          max_distance_value = static_cast<double>(p.as_int());
          RCLCPP_WARN(
              this->get_logger(),
              "parameter 'max_distance' is integer; interpreting as %.2f",
              max_distance_value);
          break;
        default:
          RCLCPP_WARN(this->get_logger(),
                      "parameter 'max_distance' has unexpected type %d",
                      p.get_type());
          break;
      }
      RCLCPP_INFO(this->get_logger(), "  max_distance: %.2f",
                  max_distance_value);
    }

    // 创建参数事件订阅器，监听参数变化
    param_event_sub_ =
        this->create_subscription<rcl_interfaces::msg::ParameterEvent>(
            "/parameter_events", 10,
            std::bind(&ParamsServer::param_event_callback, this,
                      std::placeholders::_1));

    // 创建定时器，定期显示参数值
    timer_ =
        this->create_wall_timer(std::chrono::seconds(5),
                                std::bind(&ParamsServer::timer_callback, this));

    print_usage();
  }

 private:
  void param_event_callback(
      const rcl_interfaces::msg::ParameterEvent::SharedPtr msg) {
    if (!msg->changed_parameters.empty()) {
      RCLCPP_INFO(this->get_logger(), "\n--- Parameters Changed ---");
      for (const auto& param : msg->changed_parameters) {
        RCLCPP_INFO(this->get_logger(), "Parameter '%s' changed",
                    param.name.c_str());
        // Use the type field to determine the value type (use enum constants)
        switch (param.value.type) {
          case rcl_interfaces::msg::ParameterType::PARAMETER_STRING:
            RCLCPP_INFO(this->get_logger(), "  New value: %s",
                        param.value.string_value.c_str());
            break;
          case rcl_interfaces::msg::ParameterType::PARAMETER_INTEGER:
            RCLCPP_INFO(this->get_logger(), "  New value: %lld",
                        static_cast<long long>(param.value.integer_value));
            break;
          case rcl_interfaces::msg::ParameterType::PARAMETER_DOUBLE:
            RCLCPP_INFO(this->get_logger(), "  New value: %.2f",
                        param.value.double_value);
            break;
          case rcl_interfaces::msg::ParameterType::PARAMETER_BOOL:
            RCLCPP_INFO(this->get_logger(), "  New value: %s",
                        param.value.bool_value ? "true" : "false");
            break;
          default:
            RCLCPP_WARN(this->get_logger(), "  Unknown parameter type: %d",
                        param.value.type);
            break;
        }
      }
    }
  }

  void timer_callback() {
    RCLCPP_INFO(this->get_logger(), "\n--- Current Parameter Values ---");
    RCLCPP_INFO(this->get_logger(), "  device_name: %s",
                this->get_parameter("device_name").as_string().c_str());
    RCLCPP_INFO(
        this->get_logger(), "  update_rate: %lld",
        static_cast<long long>(this->get_parameter("update_rate").as_int()));
    RCLCPP_INFO(
        this->get_logger(), "  enable_debug: %s",
        this->get_parameter("enable_debug").as_bool() ? "true" : "false");
    {
      auto p = this->get_parameter("max_distance");
      double max_distance_value = 0.0;
      switch (p.get_type()) {
        case rcl_interfaces::msg::ParameterType::PARAMETER_DOUBLE:
          max_distance_value = p.as_double();
          break;
        case rcl_interfaces::msg::ParameterType::PARAMETER_INTEGER:
          max_distance_value = static_cast<double>(p.as_int());
          RCLCPP_WARN(
              this->get_logger(),
              "parameter 'max_distance' is integer; interpreting as %.2f",
              max_distance_value);
          break;
        default:
          RCLCPP_WARN(this->get_logger(),
                      "parameter 'max_distance' has unexpected type %d",
                      p.get_type());
          break;
      }
      RCLCPP_INFO(this->get_logger(), "  max_distance: %.2f",
                  max_distance_value);
    }
  }

  void print_usage() {
    RCLCPP_INFO(this->get_logger(),
                "\n========================================");
    RCLCPP_INFO(this->get_logger(), "Available CLI Commands:");
    RCLCPP_INFO(this->get_logger(), "========================================");
    RCLCPP_INFO(this->get_logger(), "\n1. List all parameters:");
    RCLCPP_INFO(this->get_logger(), "   ros2 param list");

    RCLCPP_INFO(this->get_logger(), "\n2. Get a specific parameter:");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param get /params_server device_name");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param get /params_server update_rate");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param get /params_server enable_debug");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param get /params_server max_distance");

    RCLCPP_INFO(this->get_logger(), "\n3. Set a string parameter:");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param set /params_server device_name my_device");

    RCLCPP_INFO(this->get_logger(), "\n4. Set an integer parameter:");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param set /params_server update_rate 20");

    RCLCPP_INFO(this->get_logger(), "\n5. Set a boolean parameter:");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param set /params_server enable_debug true");

    RCLCPP_INFO(this->get_logger(), "\n6. Set a float parameter:");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param set /params_server max_distance 50.5");

    RCLCPP_INFO(this->get_logger(), "\n7. Load parameters from YAML file:");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param load /params_server params.yaml");

    RCLCPP_INFO(this->get_logger(), "\n8. Save parameters to YAML file:");
    RCLCPP_INFO(this->get_logger(),
                "   ros2 param dump /params_server > params.yaml");

    RCLCPP_INFO(this->get_logger(),
                "\n========================================\n");
  }

  rclcpp::Subscription<rcl_interfaces::msg::ParameterEvent>::SharedPtr
      param_event_sub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ParamsServer>());
  rclcpp::shutdown();
  return 0;
}
