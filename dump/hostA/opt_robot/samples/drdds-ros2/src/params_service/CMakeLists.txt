cmake_minimum_required(VERSION 3.5)
project(params_service)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rcl_interfaces REQUIRED)

# Build C++ parameter server example
add_executable(params_server_cpp src/params_server.cpp)

ament_target_dependencies(params_server_cpp
  rclcpp
  rcl_interfaces
)

install(TARGETS params_server_cpp
  DESTINATION lib/${PROJECT_NAME}
)

# Install Python scripts
install(PROGRAMS
  src/params_server.py
  src/params_client.py
  src/advanced_params_example.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY
  launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Install config files
install(DIRECTORY
  config/
  DESTINATION share/${PROJECT_NAME}/config
)

# Install documentation
install(FILES
  README.md
  CLI_REFERENCE.md
  QUICKSTART.sh
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
