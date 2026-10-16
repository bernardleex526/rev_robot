#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/msg/point_field.hpp>
#include <cmath>
#include <vector>
#include <cstring>

class LidarPublisher : public rclcpp::Node {
public:
    LidarPublisher() : Node("lidar_publisher"), counter_(0) {
        // 使用尽力传输QoS
        rclcpp::QoS qos_profile = rclcpp::QoS(rclcpp::KeepLast(10));
        qos_profile.best_effort();
        
        publisher_ = this->create_publisher<sensor_msgs::msg::PointCloud2>("/LIDAR_POINTS", qos_profile);
        // Create a 10Hz timer (0.1 seconds)
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100),  // 100ms = 10Hz
            std::bind(&LidarPublisher::timer_callback, this));
    }

private:
    void timer_callback() {
        // Create point cloud with 170 points
        const size_t num_points = 170;
        
        // Generate point cloud data
        auto points = generate_point_cloud(num_points, counter_);
        
        // Create PointCloud2 message
        auto msg = create_pointcloud2_msg(points);
        
        // Publish the message
        publisher_->publish(msg);
        RCLCPP_INFO(this->get_logger(), "Published point cloud with %zu points", num_points);
        counter_++;
    }
    
    std::vector<std::vector<float>> generate_point_cloud(size_t num_points, int counter) {
        /*
         * Generate sample point cloud data with specified number of points
         */
        std::vector<std::vector<float>> points;
        
        for (size_t i = 0; i < num_points; i++) {
            // Create a spiral pattern
            double angle = (i / 1000.0) + (counter / 10.0);
            double radius = 5.0 + (i % 100) / 20.0;
            double x = radius * std::cos(angle);
            double y = radius * std::sin(angle);
            double z = (i % 50) / 10.0 - 2.5;  // Range from -2.5 to 2.5
            
            // Add some intensity value (0-255)
            float intensity = static_cast<float>((std::sin(angle) + 1) * 127.5);
            
            points.push_back({static_cast<float>(x), static_cast<float>(y), static_cast<float>(z), intensity});
        }
        
        return points;
    }
    
    sensor_msgs::msg::PointCloud2 create_pointcloud2_msg(const std::vector<std::vector<float>>& points) {
        /*
         * Create PointCloud2 message from points array
         * Each point has x, y, z coordinates and intensity
         */
        sensor_msgs::msg::PointCloud2 msg;
        
        // Set header
        msg.header.stamp = this->get_clock()->now();
        msg.header.frame_id = "lidar_frame";
        
        // Define point fields (x, y, z, intensity)
        sensor_msgs::msg::PointField x_field;
        x_field.name = "x";
        x_field.offset = 0;
        x_field.datatype = sensor_msgs::msg::PointField::FLOAT32;
        x_field.count = 1;
        
        sensor_msgs::msg::PointField y_field;
        y_field.name = "y";
        y_field.offset = 4;
        y_field.datatype = sensor_msgs::msg::PointField::FLOAT32;
        y_field.count = 1;
        
        sensor_msgs::msg::PointField z_field;
        z_field.name = "z";
        z_field.offset = 8;
        z_field.datatype = sensor_msgs::msg::PointField::FLOAT32;
        z_field.count = 1;
        
        sensor_msgs::msg::PointField intensity_field;
        intensity_field.name = "intensity";
        intensity_field.offset = 12;
        intensity_field.datatype = sensor_msgs::msg::PointField::FLOAT32;
        intensity_field.count = 1;
        
        msg.fields = {x_field, y_field, z_field, intensity_field};
        
        // Set point properties
        msg.height = 1;
        msg.width = points.size();
        msg.point_step = 16;  // 4 floats (x,y,z,intensity) * 4 bytes each
        msg.row_step = msg.point_step * msg.width;
        msg.is_dense = true;  // No invalid points
        
        // Pack data into binary format
        std::vector<uint8_t> buffer;
        for (const auto& point : points) {
            for (float value : point) {
                uint8_t float_bytes[4];
                std::memcpy(float_bytes, &value, sizeof(float));
                buffer.insert(buffer.end(), float_bytes, float_bytes + 4);
            }
        }
        
        msg.data = buffer;
        
        return msg;
    }
    
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    int counter_;
};

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<LidarPublisher>());
    rclcpp::shutdown();
    return 0;
}