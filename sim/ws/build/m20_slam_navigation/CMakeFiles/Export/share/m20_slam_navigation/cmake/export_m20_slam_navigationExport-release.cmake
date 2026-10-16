#----------------------------------------------------------------
# Generated CMake target import file for configuration "Release".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "m20_slam_navigation::m20_slam_core" for configuration "Release"
set_property(TARGET m20_slam_navigation::m20_slam_core APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(m20_slam_navigation::m20_slam_core PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libm20_slam_core.so"
  IMPORTED_SONAME_RELEASE "libm20_slam_core.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS m20_slam_navigation::m20_slam_core )
list(APPEND _IMPORT_CHECK_FILES_FOR_m20_slam_navigation::m20_slam_core "${_IMPORT_PREFIX}/lib/libm20_slam_core.so" )

# Import target "m20_slam_navigation::m20_drdds_input" for configuration "Release"
set_property(TARGET m20_slam_navigation::m20_drdds_input APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(m20_slam_navigation::m20_drdds_input PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libm20_drdds_input.so"
  IMPORTED_SONAME_RELEASE "libm20_drdds_input.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS m20_slam_navigation::m20_drdds_input )
list(APPEND _IMPORT_CHECK_FILES_FOR_m20_slam_navigation::m20_drdds_input "${_IMPORT_PREFIX}/lib/libm20_drdds_input.so" )

# Import target "m20_slam_navigation::m20_pointcloud_wire" for configuration "Release"
set_property(TARGET m20_slam_navigation::m20_pointcloud_wire APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(m20_slam_navigation::m20_pointcloud_wire PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libm20_pointcloud_wire.so"
  IMPORTED_SONAME_RELEASE "libm20_pointcloud_wire.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS m20_slam_navigation::m20_pointcloud_wire )
list(APPEND _IMPORT_CHECK_FILES_FOR_m20_slam_navigation::m20_pointcloud_wire "${_IMPORT_PREFIX}/lib/libm20_pointcloud_wire.so" )

# Import target "m20_slam_navigation::m20_socket_input" for configuration "Release"
set_property(TARGET m20_slam_navigation::m20_socket_input APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(m20_slam_navigation::m20_socket_input PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "m20_slam_navigation::m20_pointcloud_wire"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libm20_socket_input.so"
  IMPORTED_SONAME_RELEASE "libm20_socket_input.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS m20_slam_navigation::m20_socket_input )
list(APPEND _IMPORT_CHECK_FILES_FOR_m20_slam_navigation::m20_socket_input "${_IMPORT_PREFIX}/lib/libm20_socket_input.so" )

# Import target "m20_slam_navigation::m20_native_navigation_bridge" for configuration "Release"
set_property(TARGET m20_slam_navigation::m20_native_navigation_bridge APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(m20_slam_navigation::m20_native_navigation_bridge PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_RELEASE "pcl_common;pcl_kdtree;pcl_octree;pcl_search;pcl_sample_consensus;pcl_filters;pcl_io;pcl_features;pcl_ml;pcl_segmentation;pcl_visualization;pcl_surface;pcl_registration;pcl_keypoints;pcl_tracking;pcl_recognition;pcl_stereo;pcl_apps;pcl_outofcore;pcl_people;Boost::system;Boost::filesystem;Boost::date_time;Boost::iostreams;Boost::serialization;VTK::ChartsCore;VTK::CommonColor;VTK::CommonComputationalGeometry;VTK::CommonCore;VTK::CommonDataModel;VTK::CommonExecutionModel;VTK::CommonMath;VTK::CommonMisc;VTK::CommonTransforms;VTK::FiltersCore;VTK::FiltersExtraction;VTK::FiltersGeneral;VTK::FiltersGeometry;VTK::FiltersModeling;VTK::FiltersSources;VTK::ImagingCore;VTK::ImagingSources;VTK::InteractionImage;VTK::InteractionStyle;VTK::InteractionWidgets;VTK::IOCore;VTK::IOGeometry;VTK::IOImage;VTK::IOLegacy;VTK::IOPLY;VTK::RenderingAnnotation;VTK::RenderingCore;VTK::RenderingContext2D;VTK::RenderingLOD;VTK::RenderingFreeType;VTK::ViewsCore;VTK::ViewsContext2D;VTK::RenderingOpenGL2;VTK::GUISupportQt;FLANN::FLANN"
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libm20_native_navigation_bridge.so"
  IMPORTED_SONAME_RELEASE "libm20_native_navigation_bridge.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS m20_slam_navigation::m20_native_navigation_bridge )
list(APPEND _IMPORT_CHECK_FILES_FOR_m20_slam_navigation::m20_native_navigation_bridge "${_IMPORT_PREFIX}/lib/libm20_native_navigation_bridge.so" )

# Import target "m20_slam_navigation::slam_node_component" for configuration "Release"
set_property(TARGET m20_slam_navigation::slam_node_component APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(m20_slam_navigation::slam_node_component PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libslam_node_component.so"
  IMPORTED_SONAME_RELEASE "libslam_node_component.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS m20_slam_navigation::slam_node_component )
list(APPEND _IMPORT_CHECK_FILES_FOR_m20_slam_navigation::slam_node_component "${_IMPORT_PREFIX}/lib/libslam_node_component.so" )

# Import target "m20_slam_navigation::localization_node_component" for configuration "Release"
set_property(TARGET m20_slam_navigation::localization_node_component APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(m20_slam_navigation::localization_node_component PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/liblocalization_node_component.so"
  IMPORTED_SONAME_RELEASE "liblocalization_node_component.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS m20_slam_navigation::localization_node_component )
list(APPEND _IMPORT_CHECK_FILES_FOR_m20_slam_navigation::localization_node_component "${_IMPORT_PREFIX}/lib/liblocalization_node_component.so" )

# Import target "m20_slam_navigation::navigation_node_component" for configuration "Release"
set_property(TARGET m20_slam_navigation::navigation_node_component APPEND PROPERTY IMPORTED_CONFIGURATIONS RELEASE)
set_target_properties(m20_slam_navigation::navigation_node_component PROPERTIES
  IMPORTED_LOCATION_RELEASE "${_IMPORT_PREFIX}/lib/libnavigation_node_component.so"
  IMPORTED_SONAME_RELEASE "libnavigation_node_component.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS m20_slam_navigation::navigation_node_component )
list(APPEND _IMPORT_CHECK_FILES_FOR_m20_slam_navigation::navigation_node_component "${_IMPORT_PREFIX}/lib/libnavigation_node_component.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
