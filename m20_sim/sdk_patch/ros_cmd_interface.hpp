// ros_cmd_interface.hpp
// User command source driven by a ROS 2 topic, for headless/WSL simulation.
//   /sim_cmd (geometry_msgs/Twist): linear.x/linear.y/angular.z = forward/side/yaw scale in [-1,1]
//   /sim_mode (std_msgs/UInt8):     1 = stand up, 6 = RL control, 2 = joint damping
#pragma once

#include "user_command_interface.h"
#include "custom_types.h"
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <std_msgs/msg/u_int8.hpp>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <iostream>
#include <mutex>
#include <thread>

using namespace interface;
using namespace types;

class RosCmdInterface : public UserCommandInterface
{
private:
    std::shared_ptr<rclcpp::Node> node_;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr twist_sub_;
    rclcpp::Subscription<std_msgs::msg::UInt8>::SharedPtr mode_sub_;
    std::thread spin_thread_;
    std::atomic<bool> running_{false};
    std::mutex mtx_;
    double last_twist_time_ = 0.0;
    // zero the velocity if no /sim_cmd arrives for this long, as a dead-man switch
    static constexpr double kCmdTimeout = 0.5;

    static double Now()
    {
        return std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count() / 1e6;
    }

    void OnTwist(const geometry_msgs::msg::Twist::SharedPtr msg)
    {
        std::lock_guard<std::mutex> lk(mtx_);
        usr_cmd_->forward_vel_scale  = std::clamp<float>(msg->linear.x,  -1.f, 1.f);
        usr_cmd_->side_vel_scale     = std::clamp<float>(msg->linear.y,  -1.f, 1.f);
        usr_cmd_->turnning_vel_scale = std::clamp<float>(msg->angular.z, -1.f, 1.f);
        last_twist_time_ = Now();
    }

    void OnMode(const std_msgs::msg::UInt8::SharedPtr msg)
    {
        std::lock_guard<std::mutex> lk(mtx_);
        const uint8_t cur = msfb_->GetCurrentState();
        const uint8_t m = msg->data;
        if (m == uint8_t(RobotMotionState::JointDamping)) {
            usr_cmd_->target_mode = m;
        } else if (m == uint8_t(RobotMotionState::StandingUp) && cur == uint8_t(RobotMotionState::WaitingForStand)) {
            usr_cmd_->target_mode = m;
        } else if (m == uint8_t(RobotMotionState::RLControlMode) && cur == uint8_t(RobotMotionState::StandingUp)) {
            usr_cmd_->target_mode = m;
        } else {
            std::cout << "[RosCmd] mode " << int(m) << " rejected in state " << int(cur) << std::endl;
            return;
        }
        std::cout << "[RosCmd] target_mode -> " << int(m) << std::endl;
    }

public:
    explicit RosCmdInterface(RobotName robot_name) : UserCommandInterface(robot_name)
    {
        std::memset(usr_cmd_, 0, sizeof(UserCommand));
    }

    ~RosCmdInterface() override { Stop(); }

    void Start() override
    {
        if (running_) return;
        running_ = true;
        node_ = std::make_shared<rclcpp::Node>("rl_deploy_ros_cmd");
        twist_sub_ = node_->create_subscription<geometry_msgs::msg::Twist>(
            "/sim_cmd", 10, std::bind(&RosCmdInterface::OnTwist, this, std::placeholders::_1));
        mode_sub_ = node_->create_subscription<std_msgs::msg::UInt8>(
            "/sim_mode", 10, std::bind(&RosCmdInterface::OnMode, this, std::placeholders::_1));
        spin_thread_ = std::thread([this] {
            rclcpp::executors::SingleThreadedExecutor exec;
            exec.add_node(node_);
            while (running_ && rclcpp::ok()) {
                exec.spin_some(std::chrono::milliseconds(10));
                {
                    std::lock_guard<std::mutex> lk(mtx_);
                    if (Now() - last_twist_time_ > kCmdTimeout) {
                        usr_cmd_->forward_vel_scale = usr_cmd_->side_vel_scale = usr_cmd_->turnning_vel_scale = 0.f;
                    }
                    usr_cmd_->time_stamp = Now();
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(2));
            }
        });
        std::cout << "[RosCmdInterface] listening on /sim_cmd (Twist) and /sim_mode (UInt8: 1 stand, 6 RL, 2 damping)" << std::endl;
    }

    void Stop() override
    {
        if (!running_) return;
        running_ = false;
        if (spin_thread_.joinable()) spin_thread_.join();
    }

    UserCommand* GetUserCommand() override { return usr_cmd_; }
};
