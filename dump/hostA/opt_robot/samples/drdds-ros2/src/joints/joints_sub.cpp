#include "drdds/msg/joints_data.hpp"
#include <rclcpp/rclcpp.hpp>
#include <stdio.h>

class JointsDataSubscriber : public rclcpp::Node {
public:
  JointsDataSubscriber() : Node("jointsdata_subscriber") {
    subscription_ = this->create_subscription<drdds::msg::JointsData>(
        "/JOINTS_DATA", 10,
        std::bind(&JointsDataSubscriber::topic_callback, this,
                  std::placeholders::_1));
  }

private:
  void topic_callback(const drdds::msg::JointsData::SharedPtr msg) const {
    printf("Received JointsData message:%ld\n", msg->data.joints_data.size());
    for (auto joint : msg->data.joints_data) {
      printf(" - Position: %f, torque: %f, velocity: %f\n", joint.position,
             joint.torque, joint.velocity);
    }
  }
  rclcpp::Subscription<drdds::msg::JointsData>::SharedPtr subscription_;
};

int main(int argc, char *argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<JointsDataSubscriber>());
  rclcpp::shutdown();
  return 0;
}
