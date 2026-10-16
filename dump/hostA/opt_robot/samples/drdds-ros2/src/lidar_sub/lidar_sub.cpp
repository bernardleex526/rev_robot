#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <stdio.h>
#include <chrono>

class PointCloudSubscriber : public rclcpp::Node {
public:
  PointCloudSubscriber() : Node("pointcloud_subscriber") {
    // 使用尽力传输QoS
    rclcpp::QoS qos_profile = rclcpp::QoS(rclcpp::KeepLast(10));
    qos_profile.best_effort();
    
    subscription_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
        "/LIDAR_POINTS", qos_profile,
        std::bind(&PointCloudSubscriber::topic_callback, this,
                  std::placeholders::_1));
  }

private:
  void
  topic_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg) const {
    // 计算消息延迟 - 使用标准库获取系统时间
    auto current_time = std::chrono::system_clock::now();
    // 将ROS2时间转换为标准库时间点进行计算
    auto msg_time_point = std::chrono::time_point<std::chrono::system_clock, std::chrono::nanoseconds>(
        std::chrono::seconds(msg->header.stamp.sec) + std::chrono::nanoseconds(msg->header.stamp.nanosec)
    );
    
    // 计算时间差（秒为单位）
    double delay = std::chrono::duration<double>(current_time - msg_time_point).count();
    
    RCLCPP_INFO(this->get_logger(), "Received message with delay: %.6f seconds", delay);
    RCLCPP_INFO(this->get_logger(), "Width: %u, Height: %u", msg->width, msg->height);
    RCLCPP_INFO(this->get_logger(), "Point step: %u, Row step: %u", msg->point_step, msg->row_step);
    
    for (const auto &field : msg->fields) {
      RCLCPP_INFO(this->get_logger(), " - Name: %s, Offset: %u, Datatype: %u, Count: %u",
             field.name.c_str(), field.offset, field.datatype, field.count);
    }
  }
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr subscription_;
};

int main(int argc, char *argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PointCloudSubscriber>());
  rclcpp::shutdown();
  return 0;
}