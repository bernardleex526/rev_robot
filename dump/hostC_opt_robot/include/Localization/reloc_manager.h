#ifndef Localization_RELOC_MANAGER_H_
#define Localization_RELOC_MANAGER_H_
#include <thread>
#include "Localization/common.h"
#include "RobotLib/robot_lib.h"

namespace graph_loc {
using namespace robot_lib;

template<typename PointCloudT>
class RelocManager {
public:
    std::pair<int, Pose> runReloc(typename PointCloudT::Ptr current_cloud, Pose initial_pose);

    /**
     * -2: 正在执行，-1：失败，0-100：正常
     */
    RelocManager();

private:
    std::pair<int, Pose> runReloc(typename PointCloudT::Ptr current_cloud, std::optional<Pose> initial_pose);
    template <typename T>
    struct Data {
        T data;
        double timestamp;
        std::mutex lock;
        Data() {
            lock.lock();
            data.reset();
            timestamp = 0.0;
            lock.unlock();
        }
    };

    struct DataGroup {
        Data<typename PointCloudT::Ptr> lidar;
    } data_group_;

    std::atomic<bool> relocing_;  // false：空闲，true：正在执行
    std::shared_ptr<DrLogger> logger_;
};
}  // namespace graph_loc
#endif  // Localization_RELOC_MANAGER_H_