#ifndef Localization_MONITOR_H_
#define Localization_MONITOR_H_
#include <thread>
#include "RobotLib/robot_lib.h"

namespace graph_loc {
using namespace robot_lib;

class LocalizationMonitor {
public:
    struct DetailStatus {
        std::uint8_t
            total_status;  // 总体状态  0：正常  1：初始化  2：存在一些异常，但不影响功能，可忽略   3：定位丢失，正在自行尝试重定位    4：定位丢失，但为其它模块问题，解决对应模块问题后，定位可自行恢复    5： 定位丢失（或重定位失败），需手动指定初始位姿     6：定位丢失，需重启定位程序
        struct InputStatus {                // 输入源状态  0：不使用  1：正常使用  2：无数据输入  3：数据异常，不使用
            std::uint8_t lidar;             // 雷达
            std::uint8_t imu;               // imu
            std::uint8_t leg_odom;          // 足式里程计
            std::uint8_t rtk;               // rtk
            std::uint8_t tag;               // 已知绝对位置的各种标记物，包括充电桩反光柱、二维码等等
            std::uint8_t reflective_strip;  // 反光条
        } input_status;

        struct LossStatus {               // 丢失检测状态  0：正常  1：存在异常，但程度不高，仍可运行  2：异常，判断为定位丢失
            std::uint8_t odom_error;      // 帧间里程计误差状态
            std::uint8_t leg_odom_error;  // 与足式里程计误差状态
            std::uint8_t matching_error;  // 点云匹配误差状态
            std::uint8_t pub_error;       // 定位结果发布状态（是否持续有值发布）
        } loss_status;

        struct ExecStatus {                // 执行中的其它状态或异常
            std::uint8_t overtime;         // 处理超时状态  0：正常  1：超时
            std::uint8_t numeric_error;    // 处理过程中数值异常  0：正常  1：数值异常
            std::uint8_t timestamp_error;  // 处理过程中时间戳异常  0：正常  1：时间戳异常（跳变、回退等）
            std::uint8_t mode;             // 定位模式  0：有图  1：无图
        } exec_status;
    };

    struct LocalizationMonitorParam {
        int state_win_size;         // 状态值留存窗口大小
        int error_win_size;         // 状态误差值留存数量窗口大小
        double vel_check_duration;  // 用于判断状态速度值是否异常的时间窗口大小
        double vel_linear_limit;    // 线速度判断阈值大小
        double vel_angular_limit;   // 角速度判断阈值大小

        double vel_error_frac_th;  // 用于状态值判断的时间窗口中，速度误差过大的比例阈值

        double predict_error_check_duration;  // 与imu预测值判断的时间窗口大小
        double error_linear_limit;            // 与imu预测值判断的平移误差阈值（m）
        double error_angular_limit;           // 与imu预测值判断的旋转误差阈值（rad）
        double predict_error_frac_th;         // 用于与imu预测值判断的时间窗口中，误差过大的比例阈值

        int matching_error_win_size;           // 匹配误差数据留存帧数窗口大小
        double matching_error_check_duration;  // 匹配误差数据检查时间窗口
        double matching_error_frac_th;         // 匹配误差数据异常比例阈值
        double matching_error_th;              // 匹配误差阈值
        double inlier_ratio_th;                // 内点比例阈值

        double odom_update_time_limit;  // 定位结果更新超时检查阈值

        double found_judge_time_limit;  // 定位恢复正常的判断时间阈值

        bool auto_reloc;
        double reloc_loss_time;        // 丢失超过一定时间后自动重定位
        double reloc_loss_again_time;  // 恢复定位超过一定时间再次丢失后自动重定位
    };

    typedef std::function<void(DetailStatus)> StatusPubFunction;
    typedef std::function<void(std::uint16_t)> ErrorCodePubFunction;
    typedef std::function<bool(robot_lib::State)> RelocFunction;

    LocalizationMonitor(LocalizationMonitorParam& params);
    ~LocalizationMonitor();
    void setStatusPubCallback(StatusPubFunction func);
    void setErrorCodePubCallback(ErrorCodePubFunction func);
    void setRelocCallback(RelocFunction func);

    void pushOdomData(robot_lib::State current_state, robot_lib::State predict_state);  // 传入用于定位丢失判断的当前帧定位数据和（与当前帧最接近的）足式里程计数据
    void pushMatchingErrorData(double matching_error_current, double inlier_frac_current);  // 传入用于定位丢失判断的匹配误差数据

    void pushInputStatus(int source, int status);
    void pushExecStatus(int exec, int status);
    void reset();
    void setTotalStatus(int status, double duration);

    void exit();

private:
    class LocalizationMonitorImpl;
    std::unique_ptr<LocalizationMonitorImpl> pimpl_;
};

}  // namespace graph_loc

#endif  // Localization_MONITOR_H_