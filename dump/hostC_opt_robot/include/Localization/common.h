#ifndef Localization_COMMON_H_
#define Localization_COMMON_H_
#include <Eigen/Core>
#include <Eigen/Geometry>

#include <pcl/filters/voxel_grid.h>
#include <pcl/io/pcd_io.h>
#include <pcl/octree/octree.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>

#include <gtsam/geometry/Pose3.h>
#include <gtsam/geometry/Rot3.h>
#include <gtsam/inference/Symbol.h>
#include <gtsam/navigation/ImuFactor.h>
#include <gtsam/nonlinear/Marginals.h>
#include <gtsam/nonlinear/NonlinearFactorGraph.h>
#include <gtsam/nonlinear/Values.h>
#include <gtsam/slam/BetweenFactor.h>
#include <gtsam/slam/PriorFactor.h>

#include <cmath>
#include <condition_variable>
#include <iostream>
#include <memory>
#include <mutex>


#include "log4cplus_dr/dr_logger.hpp"

namespace graph_loc {


using gtsam::symbol_shorthand::B;  // IMU bias
using gtsam::symbol_shorthand::V;  // IMU velocity
using gtsam::symbol_shorthand::X;  // IMU pose

// using namespace robot_lib;

}  // namespace graph_loc

#endif  // Localization_COMMON_H_