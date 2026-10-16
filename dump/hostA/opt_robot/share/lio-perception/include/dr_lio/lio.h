#ifndef DR_LIO_LIO_H
#define DR_LIO_LIO_H

#include <functional>
#include <pcl/kdtree/kdtree_flann.h>
#include <opencv2/opencv.hpp>
#include <string>
#include "voxel_block_map/public_types.h"
#include "common_lib.h"

// #include "../voxel_block_map/grid_map_publisher.h"
// session计数：自构造后开始计数，每重置一次则计数+1
// 输入：雷达imu数据包
// 输出：里程计位姿、去畸变点云（imu系）、去畸变点云（odom系）
// 重置功能(加入指定session序号参数)
// 输出imu预测位姿
// 结果写入文件功能
//// !!! 传入点云时确认是否已转换到imu坐标系下
namespace dr_lio {

// class LidarOdometry {
// public:
//     EIGEN_MAKE_ALIGNED_OPERATOR_NEW;

// #ifdef IVOX_NODE_TYPE_PHC
//     using IVoxType = IVox<3, IVoxNodeType::PHC, PointType>;
// #else
//     using IVoxType = IVox<3, IVoxNodeType::DEFAULT, PointType>;
// #endif

//     struct LidarOdometryParam {
//         bool extrinsic_est_en;  //
//         int max_iteration;      //
//         int ivox_nearby_type;
//         float esti_plane_threshold;  //
//         float init_time;
//         float lidar_cov;
//         float ivox_resolution;
//         double filter_size;
//         double gyr_cov;
//         double acc_cov;
//         double b_gyr_cov;
//         double b_acc_cov;
// robot_lib::M4D extrinsic_I_B;
// robot_lib::M4D extrinsic_B_L;
//     };

//     LidarOdometry(LidarOdometryParam& params, robot_lib::State& init_state, bool align_grav = true);

//     bool run(robot_lib::MeasureGroup<robot_lib::CloudData<PointType>, robot_lib::ImuData>::Ptr measure);
//     void reset(robot_lib::State init_state);

//     void getState(robot_lib::State& state) {
//         state.pos.t(0) = state_point_.pos(0);
//         state.pos.t(1) = state_point_.pos(1);
//         state.pos.t(2) = state_point_.pos(2);
//         state.pos.R = state_point_.rot.toRotationMatrix();
//         state.vel = state_point_.vel;
//         state.bias.bias_gyr = state_point_.bg;
//         state.bias.bias_acc = state_point_.ba;
//         // out.pose.orientation.y = state_point_.rot.coeffs()[1];
//         // out.pose.orientation.z = state_point_.rot.coeffs()[2];
//         // out.pose.orientation.w = state_point_.rot.coeffs()[3];
//     }
//     void getStatePredicted(robot_lib::State& state) {
//         state.pos.t(0) = state_predicted_.pos(0);
//         state.pos.t(1) = state_predicted_.pos(1);
//         state.pos.t(2) = state_predicted_.pos(2);
//         state.pos.R = state_predicted_.rot.toRotationMatrix();
//         state.vel = state_predicted_.vel;
//         state.bias.bias_gyr = state_predicted_.bg;
//         state.bias.bias_acc = state_predicted_.ba;
//     }
//     void getCloudRegisteredBody(typename robot_lib::CloudData<PointType>::Ptr cloud_registered_body) { cloud_registered_body->cloud = scan_down_body_; }
//     void getCloudRegistered(typename robot_lib::CloudData<PointType>::Ptr& cloud_registered) { cloud_registered->cloud = scan_down_world_; }
//     void getMatchingData(float& matching_error, float& inlier_frac) {
//         matching_error = matching_error_;
//         inlier_frac = inlier_frac_;
//     }

//     void ObsModel(state_ikfom& s, esekfom::dyn_share_datastruct<double>& ekfom_data);

//     //
//     // void getRayCastPoints(const Eigen::Vector3f& origin, const Eigen::Vector3f& norm, const float min_dist, std::vector<Eigen::Vector4f>& point_list, float max_range = 20) {
//     //     std::unique_lock<std::mutex> lock(map_mtx_);
//     //     // body->global
//     //     Eigen::Matrix3f R = state_point_.rot.toRotationMatrix().cast<float>();
//     //     Eigen::Vector3f t = state_point_.pos.cast<float>();
//     //     Eigen::Vector3f origin_global = R * origin + t;
//     //     Eigen::Vector3f norm_global = R * norm;
//     //     voxel_map->getRayCastPoints(origin_global, norm_global, 2, min_dist, point_list, max_range);
//     //     // global->body
//     //     Eigen::Matrix3f R_inverse = R.transpose();
//     //     Eigen::Vector3f t_inverse = -1.0 * R_inverse * t;
//     //     for (auto& pt : point_list) {
//     //         Eigen::Vector3f pt_tmp = R_inverse * pt.block<3, 1>(0, 0) + t_inverse;
//     //         pt.block<3, 1>(0, 0) = pt_tmp;
//     //     }
//     // }

//     std::shared_ptr<local_map::VoxelMap<PointType>> voxel_map;
//     // std::shared_ptr<local_map::HeightLayer<100, 100>> height_map;
//     // std::shared_ptr<local_map::UpdateChannels<PointType, 100, 100>> update_channel;
//     // std::shared_ptr<local_map::HeightMapPublisher<4, 80, 80>> height_map_publisher_;

//     // std::shared_ptr<map_manager::GridMapServer<PointType>> map_server_;
//     // std::shared_ptr<map_manager::VoxelMap<PointType>> voxel_map;

// private:
//     void MapIncremental();

//     void PointBodyToWorld(const PointType* pi, PointType* const po) {
//         robot_lib::V3D p_body(pi->x, pi->y, pi->z);
//         robot_lib::V3D p_global(state_point_.rot * (state_point_.offset_R_L_I * p_body + state_point_.offset_T_L_I) + state_point_.pos);

//         po->x = p_global(0);
//         po->y = p_global(1);
//         po->z = p_global(2);
//         // po->intensity = pi->intensity;
//     }
//     LidarOdometryParam params_;
//     IVoxType::Options ivox_options_;
//     // std::shared_ptr<IVoxType> ivox_ = nullptr;  // localmap in ivox

//     // std::shared_ptr<PointCloudPreprocess> preprocess_ = nullptr;  // point cloud preprocess
//     std::shared_ptr<ImuProcess> p_imu_ = nullptr;  // imu process

//     bool localmap_initialized_ = false;

//     /// point clouds data
//     PointCloudType::Ptr scan_undistort_{new PointCloudType()};                           // scan after undistortion
//     PointCloudType::Ptr scan_down_body_{new PointCloudType()};                           // downsampled scan in body
//     PointCloudType::Ptr scan_down_world_{new PointCloudType()};                          // downsampled scan in world
//     std::vector<PointVector> nearest_points_;                                            // nearest points of current scan
//     std::vector<Eigen::Vector4f, Eigen::aligned_allocator<Eigen::Vector4f>> corr_pts_;   // inlier pts
//     std::vector<Eigen::Vector4f, Eigen::aligned_allocator<Eigen::Vector4f>> corr_norm_;  // inlier plane norms
//     pcl::VoxelGrid<PointType> voxel_scan_;                                               // voxel filter for current scan
//     std::vector<float> residuals_;                                                       // point-to-plane residuals
//     std::vector<bool, Eigen::aligned_allocator<bool>> point_selected_surf_;              // selected points
//     // std::vector<bool> point_selected_surf_;
//     std::vector<Eigen::Vector4f, Eigen::aligned_allocator<Eigen::Vector4f>> plane_coef_;  // plane coeffs

//     double timediff_lidar_wrt_imu_ = 0.0;
//     double last_timestamp_lidar_ = 0;
//     double lidar_end_time_ = 0;
//     double last_timestamp_imu_ = -1.0;
//     double first_lidar_time_ = 0.0;
//     bool lidar_pushed_ = false;

//     int scan_count_ = 0;
//     int publish_count_ = 0;
//     bool flg_first_scan_ = true;
//     bool flg_EKF_inited_ = false;
//     int pcd_index_ = 0;
//     double lidar_mean_scantime_ = 0.0;
//     int scan_num_ = 0;
//     bool timediff_set_flg_ = false;
//     int effect_feat_num_ = 0;  // , frame_num_ = 0

//     std::mutex map_mtx_;

//     ///////////////////////// EKF inputs and output ///////////////////////////////////////////////////////
//     esekfom::esekf<state_ikfom, 12, input_ikfom> kf_;  // esekf
//     state_ikfom state_point_;                          // ekf current state
//     state_ikfom state_predicted_;                      // ekf predicted state
//     // vect3 pos_lidar_;                                    // lidar position after eskf update
//     // robot_lib::V3D euler_cur_ = robot_lib::V3D::Zero();  // rotation in euler angles

//     // PointCloudType::Ptr pcl_wait_save_{new PointCloudType()};  // debug save

//     // bool getParamsFromFile(std::string params_file_path);

//     float matching_error_;
//     float inlier_frac_;

//     // std::shared_ptr<map_manager::GridMap<100, 100>> grid_map_;
// };

class LidarOdometry {
public:
    // using PointType = pcl::PointXYZINormal;
    // using PointType = robot_lib::PointLabelNormal;
    // using PointCloudType = pcl::PointCloud<PointType>;
    // using CloudPtr = PointCloudType::Ptr;
    // using PointVector = std::vector<PointType, Eigen::aligned_allocator<PointType>>;

    using StatePubFunction = std::function<void(robot_lib::StateWithAngularVel)>;
                                   // 发布的状态
    using StatePubFunctionHighFrequency = std::function<void(robot_lib::StateWithAngularVel)>;
    typedef std::function<void(typename robot_lib::CloudData<PointType>::Ptr)> CloudPubFunction;  // 发布的配准点云
    // typedef std::function<void(std::shared_ptr<std::vector<robot_lib::State>>)> StateQueuePubFunction;
    using AccumulatedPointsPubFunction = std::function<void(std::shared_ptr<std::vector<Eigen::Vector3f, Eigen::aligned_allocator<Eigen::Vector3f>>>&, robot_lib::Pose, float)>;

    typedef std::function<void(std::vector<Eigen::Vector3f>&)> VoxelMapPubFunction;
    typedef std::function<void(cv::Mat&)> DepthImagePubFunction;

    // using HeightMapOutputType = local_map::GridNodeTypeTraits<local_map::GridNodeType::HEIGHT>::OutputType;
    // using HeightMapPubFunction = std::function<void(HeightMapOutputType&, Eigen::Vector4f)>;

    LidarOdometry(std::string params_file_path);
    ~LidarOdometry();

    void stop();
    void restart();

    void insertImuData(const robot_lib::ImuData::Ptr& imu_data);

    template <typename PointT>
    void insertLidarData(const typename robot_lib::CloudData<PointT>::Ptr& lidar_data, double time_offset = 0.0);

    void setStatePubCallback(StatePubFunction func);
    void setHighFrequencyOdometryPubCallback(StatePubFunctionHighFrequency func);
    void setCloudPubCallback(CloudPubFunction func);
    void setCloudBodyPubCallback(CloudPubFunction func);
    // void setStateQueuePubCallback(StateQueuePubFunction func);
    void setAccumulatedPointsPubCallback(std::uint8_t level, const Eigen::Vector3f area_min, const Eigen::Vector3f area_max, AccumulatedPointsPubFunction func);

    void setVoxelMapPubCallback(VoxelMapPubFunction func);
    void setDepthImagePubCallback(DepthImagePubFunction func);
    // void setHeightMapPubCallback(HeightMapPubFunction func);
    void addHeightMapOutputChannel(HeightMapOutputParams output_params, HeightMapOutputFunction func);

    void saveFullMap();

private:
    class LidarOdometryImpl;
    std::unique_ptr<LidarOdometryImpl> pimpl_;
};

}  // namespace dr_lio

#endif  // DR_LIO_LIO_H