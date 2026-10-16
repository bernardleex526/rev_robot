#ifndef DR_LIO_COMMON_LIB_H
#define DR_LIO_COMMON_LIB_H
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include "RobotLib/robot_lib.h"
#include "voxel_block_map/public_types.h"
namespace dr_lio {
// 内部处理点云类型
using PointType = pcl::PointXYZINormal; // robot_lib::PointLabelNormal（标签点云）
using PointCloudType = pcl::PointCloud<PointType>;
using CloudPtr = PointCloudType::Ptr;
using PointVector = std::vector<PointType, Eigen::aligned_allocator<PointType>>;

// 高度图输出类型
using HeightMapOutputType = local_map::GridNodeTypeTraits<local_map::GridNodeType::HEIGHT>::OutputType;
// 高度图输出回调函数类型
using HeightMapOutputFunction = std::function<void(HeightMapOutputType&, Eigen::Vector4f)>;
// 高度图输出参数类型
using HeightMapOutputParams = local_map::GridNodeTypeTraits<local_map::GridNodeType::HEIGHT>::OutputParams;

}  // namespace dr_lio

#endif  // DR_LIO_COMMON_LIB_H