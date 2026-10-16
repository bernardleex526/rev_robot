cmake_minimum_required(VERSION 3.5)
project(joints)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(drdds REQUIRED)

add_executable(joints_sub joints_sub.cpp)
add_executable(joints_pub joints_pub.cpp)

ament_target_dependencies(joints_sub
  rclcpp
  drdds
)

ament_target_dependencies(joints_pub
  rclcpp
  drdds
)

install(TARGETS joints_sub
  DESTINATION lib/${PROJECT_NAME}
)

install(TARGETS joints_pub
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
