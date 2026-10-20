cmake_minimum_required(VERSION 3.8)
project(m20_gazebo)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(gazebo_ros REQUIRED)
find_package(gazebo_dev REQUIRED)
find_package(drdds REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter)

add_library(m20_gazebo_bridge SHARED src/m20_gazebo_bridge.cpp)
target_compile_features(m20_gazebo_bridge PUBLIC cxx_std_17)
ament_target_dependencies(m20_gazebo_bridge rclcpp gazebo_ros gazebo_dev drdds)

set(M20_MJCF "" CACHE FILEPATH "Path to the official M20.xml (MJCF)")
if(NOT M20_MJCF)
  message(FATAL_ERROR "Pass -DM20_MJCF=/path/to/M20_description/m20_mjcf/mjcf/M20.xml")
endif()
get_filename_component(M20_MJCF_DIR ${M20_MJCF} DIRECTORY)

set(URDF_OUT ${CMAKE_CURRENT_BINARY_DIR}/m20.urdf)
add_custom_command(
  OUTPUT ${URDF_OUT}
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/scripts/mjcf_to_gazebo_urdf.py ${M20_MJCF} ${URDF_OUT}
  DEPENDS ${M20_MJCF} ${CMAKE_CURRENT_SOURCE_DIR}/scripts/mjcf_to_gazebo_urdf.py)
add_custom_target(m20_urdf ALL DEPENDS ${URDF_OUT})

install(TARGETS m20_gazebo_bridge LIBRARY DESTINATION lib)
install(FILES ${URDF_OUT} DESTINATION share/${PROJECT_NAME}/urdf)
# only the 17 robot meshes (named *.STL); the numbered *.stl belong to the MuJoCo stair scene
install(DIRECTORY ${M20_MJCF_DIR}/../meshes/ DESTINATION share/${PROJECT_NAME}/meshes FILES_MATCHING PATTERN "*.STL")
install(DIRECTORY launch worlds DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/mjcf_to_gazebo_urdf.py scripts/m20_cmd.py scripts/base_pose.py scripts/run_mujoco_bridge.py
  DESTINATION lib/${PROJECT_NAME})

ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/env-hooks/${PROJECT_NAME}.dsv.in")
ament_package()
