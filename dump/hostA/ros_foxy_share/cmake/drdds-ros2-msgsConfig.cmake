# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_drdds-ros2-msgs_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED drdds-ros2-msgs_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(drdds-ros2-msgs_FOUND FALSE)
  elseif(NOT drdds-ros2-msgs_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(drdds-ros2-msgs_FOUND FALSE)
  endif()
  return()
endif()
set(_drdds-ros2-msgs_CONFIG_INCLUDED TRUE)

# output package information
if(NOT drdds-ros2-msgs_FIND_QUIETLY)
  message(STATUS "Found drdds-ros2-msgs: 0.1.0 (${drdds-ros2-msgs_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'drdds-ros2-msgs' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${drdds-ros2-msgs_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(drdds-ros2-msgs_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${drdds-ros2-msgs_DIR}/${_extra}")
endforeach()
