#include "drdds/msg/joints_data.hpp"
#include <rclcpp/rclcpp.hpp>
#include <stdio.h>

class JointsDataPublisher : public rclcpp::Node {
public:
  JointsDataPublisher() : Node("jointsdata_publisher") {
    pub_ = this->create_publisher<drdds::msg::JointsData>("/JOINTS_CMD", 10);
    timer_ = this->create_wall_timer(
        std::chrono::milliseconds(500),
        std::bind(&JointsDataPublisher::TimerCallback, this));
  }

private:
  void TimerCallback() {
    auto msg = drdds::msg::JointsData();

    for (size_t i = 0; i < msg.data.joints_data.size(); ++i) {
      msg.data.joints_data[i].position = i * 1.0;
      msg.data.joints_data[i].torque = i * 0.1;
      msg.data.joints_data[i].velocity = i * 0.01;
    }

    RCLCPP_INFO(this->get_logger(), "Publishing joints data:");
    for (size_t i = 0; i < msg.data.joints_data.size(); ++i) {
      RCLCPP_INFO(
          this->get_logger(), "  Joint %zu: pos=%.2f, torque=%.2f, vel=%.2f", i,
          msg.data.joints_data[i].position, msg.data.joints_data[i].torque,
          msg.data.joints_data[i].velocity);
    }

    pub_->publish(msg);
  }

  rclcpp::Publisher<drdds::msg::JointsData>::SharedPtr pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char *argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<JointsDataPublisher>());
  rclcpp::shutdown();
  return 0;
}
