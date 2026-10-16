cmake_minimum_required(VERSION 3.8)
project(action_tutorial_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(example_interfaces REQUIRED)

# Create a simple fibonacci action server
add_executable(fibonacci_action_server fibonacci_action_server.cpp)
ament_target_dependencies(fibonacci_action_server
  rclcpp
  rclcpp_action
  example_interfaces)

# Create a simple fibonacci action client
add_executable(fibonacci_action_client fibonacci_action_client.cpp)
ament_target_dependencies(fibonacci_action_client
  rclcpp
  rclcpp_action
  example_interfaces)

install(TARGETS
  fibonacci_action_server
  fibonacci_action_client
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()