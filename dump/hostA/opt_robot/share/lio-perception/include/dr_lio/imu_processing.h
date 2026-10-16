#ifndef DR_LIO_IMU_PROCESSING_H
#define DR_LIO_IMU_PROCESSING_H

// #include <nav_msgs/Odometry.h>
// #include <sensor_msgs/Imu.h>
// #include <sensor_msgs/PointCloud2.h>
#include <cmath>
#include <deque>
#include <fstream>

#include "common_lib.h"
#include "so3_math.h"
#include "use-ikfom.h"
#include "RobotLib/robot_lib.h"
// #include "utils.h"
// #include <tf/transform_datatypes.h>
// #include <tf_conversions/tf_eigen.h>

namespace dr_lio {

constexpr int MAX_INI_COUNT = 200;

/// IMU Process and undistortion
class ImuProcess {
public:
    EIGEN_MAKE_ALIGNED_OPERATOR_NEW

    ImuProcess(bool align_grav = true);
    ~ImuProcess();

    static bool time_list(const PointType& x, const PointType& y) { return (x.curvature < y.curvature); };

    void Reset();
    void SetExtrinsic(const robot_lib::M4D& trans);
    void SetGyrCov(const robot_lib::V3D& scaler);
    void SetAccCov(const robot_lib::V3D& scaler);
    void SetGyrBiasCov(const robot_lib::V3D& b_g);
    void SetAccBiasCov(const robot_lib::V3D& b_a);
    void Process(const robot_lib::MeasureGroup<robot_lib::CloudData<PointType>, robot_lib::ImuData>::Ptr& meas, esekfom::esekf<state_ikfom, 12, input_ikfom>& kf_state, PointCloudType::Ptr pcl_un_);

    std::ofstream fout_imu_;
    Eigen::Matrix<double, 12, 12> Q_;
    robot_lib::V3D cov_acc_;
    robot_lib::V3D cov_gyr_;
    robot_lib::V3D cov_acc_scale_;
    robot_lib::V3D cov_gyr_scale_;
    robot_lib::V3D cov_bias_gyr_;
    robot_lib::V3D cov_bias_acc_;

private:
    void IMUInit(const robot_lib::MeasureGroup<robot_lib::CloudData<PointType>, robot_lib::ImuData>::Ptr& meas, esekfom::esekf<state_ikfom, 12, input_ikfom>& kf_state, int& N);
    void UndistortPcl(const robot_lib::MeasureGroup<robot_lib::CloudData<PointType>, robot_lib::ImuData>::Ptr& meas, esekfom::esekf<state_ikfom, 12, input_ikfom>& kf_state, PointCloudType& pcl_out);

    // PointCloudType::Ptr cur_pcl_un_;
    // sensor_msgs::ImuConstPtr last_imu_;
    // std::deque<sensor_msgs::ImuConstPtr> v_imu;
    std::vector<robot_lib::State> IMUpose_;
    // std::vector<robot_lib::M3D> v_rot_pcl_;
    robot_lib::M3D Lidar_R_wrt_IMU_;
    robot_lib::V3D Lidar_T_wrt_IMU_;
    robot_lib::V3D mean_acc_;
    robot_lib::V3D mean_gyr_;
    robot_lib::V3D angvel_last_;
    robot_lib::V3D acc_s_last_;
    double last_lidar_end_time_ = 0;
    int init_iter_num_ = 1;
    bool b_first_frame_ = true;
    bool imu_need_init_ = true;
    bool align_grav_ = true;
    double G_m_s2;
};

}  // namespace dr_lio

#endif  // DR_LIO_IMU_PROCESSING_H
