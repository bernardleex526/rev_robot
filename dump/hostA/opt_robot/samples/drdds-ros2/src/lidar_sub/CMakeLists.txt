cmake_minimum_required(VERSION 3.5)
project(lidar_sub)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

add_executable(lidar_sub lidar_sub.cpp)
add_executable(lidar_pub lidar_pub.cpp)

ament_target_dependencies(lidar_sub
  rclcpp
  sensor_msgs
)

ament_target_dependencies(lidar_pub
  rclcpp
  sensor_msgs
)

install(TARGETS lidar_sub
  DESTINATION lib/${PROJECT_NAME}
)

install(TARGETS lidar_pub
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()