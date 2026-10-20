// Gazebo Classic 11 model plugin: drdds bridge for the DeepRobotics M20.
// Mirrors interface/robot/simulation/mujoco_simulation_ros2.py from the official SDK:
//   sub /JOINTS_CMD (drdds/JointsDataCmd) -> per-step torque PD in the simulator
//   pub /JOINTS_DATA (drdds/JointsData), /IMU_DATA (drdds/ImuData) at publish_rate
// Topics are in the robot's "published" joint domain; the model is in the MJCF/raw domain:
//   raw = published * JOINT_DIR + POS_OFFSET
#include <gazebo/common/Plugin.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo_ros/node.hpp>
#include <rclcpp/rclcpp.hpp>
#include <ignition/math.hh>

#include <drdds/msg/imu_data.hpp>
#include <drdds/msg/joints_data.hpp>
#include <drdds/msg/joints_data_cmd.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <mutex>
#include <sstream>
#include <string>
#include <vector>

namespace m20_gazebo
{
constexpr int kDof = 16;
constexpr std::array<double, kDof> kJointDir = {1, 1, -1, 1, 1, -1, 1, -1, -1, 1, -1, 1, -1, -1, 1, -1};
constexpr std::array<double, kDof> kPosOffsetDeg = {-25, 229, 160, 0, 25, -131, -200, 0,
                                                    -25, -229, -160, 0, 25, 131, 200, 0};
// MJCF folded-leg init pose (raw domain), same as JOINT_INIT in the SDK MuJoCo bridge
constexpr std::array<double, kDof> kJointInit = {-0.438, -1.16, 2.76, 0, 0.438, -1.16, 2.76, 0,
                                                 -0.438, 1.16, -2.76, 0, 0.438, 1.16, -2.76, 0};

class M20DrddsBridge : public gazebo::ModelPlugin
{
public:
  void Load(gazebo::physics::ModelPtr model, sdf::ElementPtr sdf) override
  {
    model_ = model;
    ros_ = gazebo_ros::Node::Get(sdf);

    std::string joint_list = sdf->HasElement("joints") ? sdf->Get<std::string>("joints") : "";
    std::istringstream iss(joint_list);
    for (std::string name; iss >> name;) {
      auto j = model_->GetJoint(name);
      if (!j) {
        RCLCPP_FATAL(ros_->get_logger(), "joint %s not found", name.c_str());
        return;
      }
      joints_.push_back(j);
    }
    if (joints_.size() != kDof) {
      RCLCPP_FATAL(ros_->get_logger(), "expected %d joints, got %zu", kDof, joints_.size());
      return;
    }
    for (int i = 0; i < kDof; ++i) {
      effort_limit_[i] = joints_[i]->GetEffortLimit(0);
      pos_offset_[i] = kPosOffsetDeg[i] / 180.0 * M_PI;
    }

    imu_link_ = model_->GetLink(sdf->HasElement("imu_link") ? sdf->Get<std::string>("imu_link") : "base_link");
    if (sdf->HasElement("imu_offset")) imu_offset_ = sdf->Get<ignition::math::Vector3d>("imu_offset");
    double rate = sdf->HasElement("publish_rate") ? sdf->Get<double>("publish_rate") : 200.0;
    publish_period_ = 1.0 / rate;

    imu_pub_ = ros_->create_publisher<drdds::msg::ImuData>("/IMU_DATA", 200);
    joints_pub_ = ros_->create_publisher<drdds::msg::JointsData>("/JOINTS_DATA", 200);
    cmd_sub_ = ros_->create_subscription<drdds::msg::JointsDataCmd>(
        "/JOINTS_CMD", 50, std::bind(&M20DrddsBridge::OnCmd, this, std::placeholders::_1));

    for (int i = 0; i < kDof; ++i) joints_[i]->SetPosition(0, kJointInit[i], true);

    update_conn_ = gazebo::event::Events::ConnectWorldUpdateBegin(std::bind(&M20DrddsBridge::OnUpdate, this));
    RCLCPP_INFO(ros_->get_logger(), "M20 drdds bridge loaded: %d joints, IMU on %s, publish %.0f Hz",
                kDof, imu_link_->GetName().c_str(), rate);
  }

private:
  void OnCmd(const drdds::msg::JointsDataCmd::SharedPtr msg)
  {
    std::lock_guard<std::mutex> lk(mtx_);
    for (int i = 0; i < kDof; ++i) {
      const auto& c = msg->data.joints_data[i];
      kp_[i] = c.kp;
      kd_[i] = c.kd;
      pos_cmd_[i] = c.position * kJointDir[i] + pos_offset_[i];
      vel_cmd_[i] = c.velocity * kJointDir[i];
      tau_ff_[i] = c.torque;
    }
  }

  void OnUpdate()
  {
    const double t = model_->GetWorld()->SimTime().Double();
    // velocity of the IMU point, differentiated per physics step: Gazebo Classic's
    // WorldLinearAccel() excludes contact/constraint forces, so it reads ~0 while standing
    {
      const auto v_imu = imu_link_->WorldLinearVel(imu_offset_);
      const double dt = t - last_vel_time_;
      if (last_vel_time_ >= 0.0 && dt > 0.0) {
        const auto a = (v_imu - last_imu_vel_) / dt;
        constexpr double alpha = 0.2;  // light low-pass against single-step contact spikes
        imu_accel_world_ = imu_accel_world_ * (1.0 - alpha) + a * alpha;
      }
      last_imu_vel_ = v_imu;
      last_vel_time_ = t;
    }
    {
      std::lock_guard<std::mutex> lk(mtx_);
      for (int i = 0; i < kDof; ++i) {
        const double q = joints_[i]->Position(0);
        const double dq = joints_[i]->GetVelocity(0);
        double tau = kp_[i] * (pos_cmd_[i] - q) + kd_[i] * (vel_cmd_[i] - dq) + tau_ff_[i];
        tau = std::clamp(tau, -effort_limit_[i], effort_limit_[i]);
        tau_applied_[i] = tau;
        joints_[i]->SetForce(0, tau);
      }
    }
    if (t - last_publish_ >= publish_period_ - 1e-9) {
      last_publish_ = t;
      Publish(t);
    }
  }

  void Publish(double t)
  {
    builtin_interfaces::msg::Time stamp;
    stamp.sec = static_cast<int32_t>(t);
    stamp.nanosec = static_cast<uint32_t>((t - stamp.sec) * 1e9);

    // IMU: orientation of the base, body-frame angular velocity and specific force at the IMU site
    const auto pose = imu_link_->WorldPose();
    const auto rot = pose.Rot();
    const auto w_body = rot.RotateVectorReverse(imu_link_->WorldAngularVel());
    const auto g = model_->GetWorld()->Gravity();
    const auto acc_body = rot.RotateVectorReverse(imu_accel_world_ - g);
    const auto euler = rot.Euler();

    drdds::msg::ImuData imu;
    imu.header.frame_id = 0;
    imu.header.stamp = stamp;
    imu.data.roll = euler.X() * 180.0 / M_PI;
    imu.data.pitch = euler.Y() * 180.0 / M_PI;
    imu.data.yaw = euler.Z() * 180.0 / M_PI;
    imu.data.omega_x = w_body.X();
    imu.data.omega_y = w_body.Y();
    imu.data.omega_z = w_body.Z();
    imu.data.acc_x = acc_body.X();
    imu.data.acc_y = acc_body.Y();
    imu.data.acc_z = acc_body.Z();
    imu_pub_->publish(imu);

    drdds::msg::JointsData js;
    js.header.frame_id = 0;
    js.header.stamp = stamp;
    for (int i = 0; i < kDof; ++i) {
      auto& j = js.data.joints_data[i];
      j.name = {32, 32, 32, 32};
      j.data_id = 0;
      j.status_word = 1;
      j.position = (joints_[i]->Position(0) - pos_offset_[i]) * kJointDir[i];
      j.velocity = joints_[i]->GetVelocity(0) * kJointDir[i];
      j.torque = tau_applied_[i] * kJointDir[i];
      j.motion_temp = 40.0;
      j.driver_temp = 45.0;
    }
    joints_pub_->publish(js);
  }

  gazebo::physics::ModelPtr model_;
  gazebo::physics::LinkPtr imu_link_;
  ignition::math::Vector3d imu_offset_{0, 0, 0};
  std::vector<gazebo::physics::JointPtr> joints_;
  gazebo_ros::Node::SharedPtr ros_;
  gazebo::event::ConnectionPtr update_conn_;
  rclcpp::Publisher<drdds::msg::ImuData>::SharedPtr imu_pub_;
  rclcpp::Publisher<drdds::msg::JointsData>::SharedPtr joints_pub_;
  rclcpp::Subscription<drdds::msg::JointsDataCmd>::SharedPtr cmd_sub_;

  std::mutex mtx_;
  std::array<double, kDof> kp_{}, kd_{}, pos_cmd_{}, vel_cmd_{}, tau_ff_{}, tau_applied_{};
  std::array<double, kDof> effort_limit_{}, pos_offset_{};
  double publish_period_ = 0.005;
  double last_publish_ = -1.0;
  ignition::math::Vector3d last_imu_vel_{0, 0, 0}, imu_accel_world_{0, 0, 0};
  double last_vel_time_ = -1.0;
};

GZ_REGISTER_MODEL_PLUGIN(M20DrddsBridge)
}  // namespace m20_gazebo
