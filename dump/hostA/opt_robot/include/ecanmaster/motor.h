#ifndef MOTOR_H_
#define MOTOR_H_
#include "types/data_structures.h"
#include "base_actor.h"

#include <iostream>
#include <algorithm>
#include <cstdint>
#include <stdio.h>
#include <string.h>
#include <sys/resource.h>    /*setrlimit */
#include <mutex>
#include <condition_variable>
#include <thread>
#include <map>
#include <ctime>
#include <signal.h>
#include <sys/time.h>
#include <inttypes.h>
#include <sys/timerfd.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <time.h>
#include <chrono>
#include <sys/timerfd.h>
#include <sys/epoll.h>
#include <functional>

namespace ecan {

class Motor : public BaseActor {
public:
    Motor(const std::string &ethname, int thread_priority, int cpu = -1, int thread_policy = SCHED_FIFO, size_t stack_size = 0);
    ~Motor();

    void GetJointsRawData(JointRawData &values);
    JointRawData& GetJointsRawData();
    void SetJointsCMD(JointRawData &values);

    double GetTimeStamp(void);
    ImuData& get_imu_data();
    BatteryInfo& GetBatteryInfo();

    void MotorEnable(const std::string &modelpara);
    void OperationModeChange(uint32_t index);
    int32_t ConfigMotor(uint32_t index, uint32_t value = 0, int id = kJointCount);
    // 注册回调函数
    template <typename T>
    void registerCallback(const std::string& key, std::function<void(const T&)> callback) {
        callback_map[key] = [callback](const void* data) {
            callback(*static_cast<const T*>(data));  // 使用 std::function 调用回调
        };
    }
    
    void BatteryChargeEnable();
    void BatteryChargeDisable();
protected:
    virtual void* RunRoutine(void*);

private:
    class MotorImpl;
    std::unique_ptr<MotorImpl> pMotorImpl;
        // 存储回调函数的map
    std::map<std::string, std::function<void(const void*)>> callback_map;
};

};  // namespace ecan

#endif
