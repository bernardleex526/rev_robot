#ifndef Localization_LOCALIZATION_H_
#define Localization_LOCALIZATION_H_

#include <functional>
#include <string>
// #include "RobotLib/robot_lib.h"
#include "Localization/monitor.h"

namespace graph_loc {

using namespace robot_lib;

class Localization {

public:
    using PointType = pcl::PointXYZINormal;
    using PointCloudType = pcl::PointCloud<PointType>;
    typedef std::function<void(robot_lib::State)> StatePubFunction;
    using StateCovPubFunction = std::function<void(robot_lib::StateCov)>;
    typedef std::function<void(typename robot_lib::CloudData<PointType>::Ptr)> CloudPubFunction;
    typedef std::function<void(std::shared_ptr<std::vector<robot_lib::State>>)> StateQueuePubFunction;
    typedef std::function<void(typename robot_lib::CloudData<PointType>::Ptr)> WorkCloudPubFunction;
    typedef std::function<void(typename robot_lib::CloudData<PointType>::Ptr)> OutlierCloudPubFunction;
    typedef std::function<void(typename robot_lib::CloudData<PointType>::Ptr)> NoplaneCloudPubFunction;
    typedef std::function<void(typename robot_lib::CloudData<PointType>::Ptr)> SampleCloudPubFunction;

    typedef std::function<void(robot_lib::StateCov)> RtkRawStatePubFunction;

    typedef std::function<void(Eigen::Vector2i, std::array<std::int8_t, 100 * 100>&)> MapDataPubFunction;
    typedef std::function<void(std::vector<Eigen::Vector3f>&)> VoxelMapPubFunction;

    using MatchingErrorPubFunction = std::function<void(float, float)>;
    using RegistrationStdPubFunction = std::function<void(Eigen::Matrix<double, 6, 1>)>;

    using MapChunkUpdateFunction = std::function<void(std::optional<Eigen::Vector3i>, std::optional<Eigen::Vector3i>, float)>;       // 要增加的区块的原点， 要删除的区块的原点，边长

    enum class RelocRange {
        ACCURATE,    // 精确的初始定位
        INACCURATE,  // 模糊的初始定位
        UNKNOWN      // 完全未知的初始定位
    };

    Localization(std::string params_file_path);
    ~Localization();

    void insertImuData(const robot_lib::ImuData::Ptr& imu_data);
    void insertRtkData(const robot_lib::GPYBMType::Ptr& rtk_data);
    void insertVigData(const robot_lib::StateCov::Ptr& vig_data);
    void insertVigRtkData(const robot_lib::StateCov::Ptr& vig_rtk_data);

    template <typename PointT>
    void insertLidarData(const typename robot_lib::CloudData<PointT>::Ptr& lidar_data);

    void setStatePubCallback(StatePubFunction func);
    void setStateRegisteredPubCallback(StateCovPubFunction func);
    void setStatePredictedPubCallback(StateCovPubFunction func);
    void setStateLidarOdomPubCallback(StateCovPubFunction func);
    void setStateExtOdomPubCallback(StateCovPubFunction func);
    void setCloudPubCallback(CloudPubFunction func);
    void setBodyCloudPubCallback(CloudPubFunction func);
    void setWorkCloudPubCallback(WorkCloudPubFunction func);
    void setOutlierCloudPubCallback(OutlierCloudPubFunction func);
    void setNoplaneCloudPubCallback(NoplaneCloudPubFunction func);
    void setSampleCloudPubCallback(SampleCloudPubFunction func);
    void setStateQueuePubCallback(StateQueuePubFunction func);

    void setRtkRawStatePubCallback(RtkRawStatePubFunction func);

    void setMonitorStatusPubCallback(LocalizationMonitor::StatusPubFunction func);
    void setMonitorErrorCodePubCallback(LocalizationMonitor::ErrorCodePubFunction func);

    void setMatchingErrorCallback(MatchingErrorPubFunction func);
    void setRegistrationStdPubCallback(RegistrationStdPubFunction func);

    void setMapChunkUpdateCallback(MapChunkUpdateFunction func);

    // void setMapDataPubCallback(MapDataPubFunction func);

    // void setVoxelMapPubCallback(VoxelMapPubFunction func);

    bool relocNoWait(robot_lib::Pose initial_pose, RelocRange reloc_range = RelocRange::ACCURATE);

    bool relocWait(robot_lib::Pose initial_pose, RelocRange reloc_range = RelocRange::INACCURATE);

    void setTotalStatus(int status, double duration);

    // void getRayCastPoints(const Eigen::Vector3f& origin, const Eigen::Vector3f& norm, const float min_dist, std::vector<Eigen::Vector4f>& point_list, float max_range = 20);

    template <typename PointT>
    typename robot_lib::CloudData<PointT>::Ptr getCloudMap(float leaf_size);

private:
    class LocalizationImpl;
    std::unique_ptr<LocalizationImpl> pimpl_;
};

}  // namespace graph_loc
#endif  // Localization_LOCALIZATION_H_