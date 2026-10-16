cmake_minimum_required(VERSION 3.5)
project(server)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(drdds REQUIRED)

add_executable(server server.cpp)

ament_target_dependencies(server
  rclcpp
  drdds
)

install(TARGETS server
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
