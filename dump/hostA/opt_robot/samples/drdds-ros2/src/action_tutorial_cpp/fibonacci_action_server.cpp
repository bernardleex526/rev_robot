#include <functional>
#include <memory>
#include <thread>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "example_interfaces/action/fibonacci.hpp"

using Fibonacci = example_interfaces::action::Fibonacci;

class FibonacciActionServer : public rclcpp::Node
{
public:
  using GoalHandleFibonacci = rclcpp_action::ServerGoalHandle<Fibonacci>;

  explicit FibonacciActionServer(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("fibonacci_action_server", options)
  {
    using namespace std::placeholders;

    this->action_server_ = rclcpp_action::create_server<Fibonacci>(
      this,
      "fibonacci",
      std::bind(&FibonacciActionServer::handle_goal, this, _1, _2),
      std::bind(&FibonacciActionServer::handle_cancel, this, _1),
      std::bind(&FibonacciActionServer::handle_accepted, this, _1));
  }

private:
  rclcpp_action::Server<Fibonacci>::SharedPtr action_server_;

  rclcpp_action::GoalResponse handle_goal(
    const rclcpp_action::GoalUUID & uuid,
    std::shared_ptr<const Fibonacci::Goal> goal)
  {
    RCLCPP_INFO(this->get_logger(), "Received goal request with order %d", goal->order);
    (void)uuid;
    return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
  }

  rclcpp_action::CancelResponse handle_cancel(
    const std::shared_ptr<GoalHandleFibonacci> goal_handle)
  {
    RCLCPP_INFO(this->get_logger(), "Received cancel request");
    (void)goal_handle;
    return rclcpp_action::CancelResponse::ACCEPT;
  }

  void execute_long_running_goal(
    std::shared_ptr<GoalHandleFibonacci> goal_handle)
  {
    RCLCPP_INFO(this->get_logger(), "Executing goal");

    // Get the goal
    auto goal = goal_handle->get_goal();
    
    // Create feedback and result
    auto feedback = std::make_shared<Fibonacci::Feedback>();
    auto result = std::make_shared<Fibonacci::Result>();

    // Initialize fibonacci sequence
    feedback->sequence = {0};
    
    if (goal->order == 0) {
      result->sequence = feedback->sequence;
      goal_handle->succeed(result);
      RCLCPP_INFO(this->get_logger(), "Goal succeeded");
      return;
    }

    if (goal->order > 0) {
      feedback->sequence.push_back(1);
    }

    // Send initial feedback
    goal_handle->publish_feedback(feedback);

    // Compute fibonacci sequence with simulated delay
    for (int i = 1; i < goal->order; ++i) {
      // Check if the goal has been canceled
      if (goal_handle->is_canceling()) {
        RCLCPP_INFO(this->get_logger(), "Goal is canceling");
        result->sequence = feedback->sequence;
        goal_handle->canceled(result);
        return;
      }

      // Calculate next fibonacci number
      int new_number = feedback->sequence[i] + feedback->sequence[i - 1];
      feedback->sequence.push_back(new_number);

      // Publish feedback
      RCLCPP_INFO(this->get_logger(), "Publishing feedback: %d", new_number);
      goal_handle->publish_feedback(feedback);

      // Simulate long-running action with sleep
      std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    }

    // Check if goal was cancelled before completion
    if (goal_handle->is_canceling()) {
      RCLCPP_INFO(this->get_logger(), "Goal is canceling");
      result->sequence = feedback->sequence;
      goal_handle->canceled(result);
      return;
    }

    // Set result and succeed
    result->sequence = feedback->sequence;
    goal_handle->succeed(result);
    RCLCPP_INFO(this->get_logger(), "Goal succeeded");
  }

  void handle_accepted(const std::shared_ptr<GoalHandleFibonacci> goal_handle)
  {
    using namespace std::placeholders;
    
    // This needs to return quickly to avoid blocking the executor
    // So spin up a new thread to execute the goal
    std::thread{std::bind(&FibonacciActionServer::execute_long_running_goal, this, _1), goal_handle}.detach();
  }
}; // class FibonacciActionServer


int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto action_server = std::make_shared<FibonacciActionServer>();

  rclcpp::spin(action_server);

  rclcpp::shutdown();
  return 0;
}