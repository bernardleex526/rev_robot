# ROS2 Action Tutorial in C++

This package demonstrates how to implement and use Actions in ROS2 with C++. It includes both an action server and an action client that communicate using the Fibonacci action from [example_interfaces](http://wiki.ros.org/example_interfaces).

## What are ROS2 Actions?

Actions are a ROS communication pattern similar to services, except actions are designed for long-running tasks. They allow clients to send goals to action servers, receive continuous feedback during goal processing, and eventually receive a result.

## Components

### Action Server (`fibonacci_action_server`)
- Implements an action server that calculates Fibonacci sequences
- Accepts goals requesting a Fibonacci sequence of a given order
- Provides feedback during computation
- Returns the final result when complete

### Action Client (`fibonacci_action_client`)
- Sends goals to the Fibonacci action server
- Receives feedback during computation
- Receives the final result when the goal is complete

## How to Build and Run

### Prerequisites
- ROS2 installed (any recent distribution like Foxy, Galactic, or Humble)
- Properly sourced ROS2 environment

### Building the Package

```bash
cd /home/feng/code/action
colcon build --packages-select action_tutorial_cpp
source install/setup.bash
```

### Running the Example

1. First, run the action server:
```bash
ros2 run action_tutorial_cpp fibonacci_action_server
```

2. In a separate terminal, run the action client:
```bash
ros2 run action_tutorial_cpp fibonacci_action_client
```

## Key Concepts Demonstrated

1. **Goal Handling**: Accepting, rejecting, or canceling goals
2. **Feedback Publishing**: Providing intermediate status updates
3. **Result Reporting**: Returning final outcomes
4. **Asynchronous Execution**: Non-blocking action handling
5. **Thread Management**: Using threads for long-running goals

## Code Structure

- [fibonacci_action_server.cpp](src/fibonacci_action_server.cpp): Implementation of the action server
- [fibonacci_action_client.cpp](src/fibonacci_action_client.cpp): Implementation of the action client
- [CMakeLists.txt](CMakeLists.txt): Build configuration
- [package.xml](package.xml): Package metadata

## Custom Action Definition

While this example uses the built-in Fibonacci action from [example_interfaces](http://wiki.ros.org/example_interfaces), you can define custom actions by creating `.action` files in an `action/` directory of your package. An action file contains three sections:
- `goal`: Request parameters sent by the client
- `result`: Final outcome returned by the server
- `feedback`: Intermediate updates sent during processing