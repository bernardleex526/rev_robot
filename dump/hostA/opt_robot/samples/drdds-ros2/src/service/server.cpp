#include "drdds/srv/std_srv_int32.hpp"
#include "rclcpp/rclcpp.hpp"

using std::placeholders::_1;
using std::placeholders::_2;

class CommandService : public rclcpp::Node {
public:
  CommandService() : Node("command_service") {
    service_ = this->create_service<drdds::srv::StdSrvInt32>(
        "/CHARGE", std::bind(&CommandService::handle_command, this, _1, _2));
    RCLCPP_INFO(this->get_logger(), "Service server ready.");
  }

private:
  void handle_command(
      const std::shared_ptr<drdds::srv::StdSrvInt32::Request> request,
      std::shared_ptr<drdds::srv::StdSrvInt32::Response> response) {
    RCLCPP_INFO(this->get_logger(), "Received command: %d", request->command);
    response->result = request->command; // 简单逻辑
    RCLCPP_INFO(this->get_logger(), "Returning result: %d", response->result);
  }

  rclcpp::Service<drdds::srv::StdSrvInt32>::SharedPtr service_;
};

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CommandService>());
  rclcpp::shutdown();
  return 0;
}
