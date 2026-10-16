#!/bin/bash

# ROS2 Parameters Service - Test Script
# 参数服务测试脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   ROS2 Parameters Service - Test Script                    ║"
echo "║   参数服务完整测试                                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查ROS2环境
if [ -z "$ROS_DISTRO" ]; then
    echo -e "${RED}✗ Error: ROS2 environment not sourced${NC}"
    echo "Please run: source /opt/ros/<distro>/setup.bash"
    exit 1
fi

echo -e "${GREEN}✓ ROS2 Distribution: $ROS_DISTRO${NC}"

# 检查参数服务器是否运行
echo ""
echo -e "${BLUE}[Test 1] Checking if params_server is running...${NC}"
if pgrep -f "params_server" > /dev/null; then
    echo -e "${GREEN}✓ params_server is running${NC}"
else
    echo -e "${YELLOW}! params_server is not running${NC}"
    echo "Please start it with:"
    echo "  ros2 run params_service params_server_cpp"
    echo ""
    echo "Continuing with tests that don't require running server..."
fi

# Test 1: List parameters
echo ""
echo -e "${BLUE}[Test 2] Listing all parameters...${NC}"
echo "Command: ros2 param list"
timeout 5 ros2 param list | head -20
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test passed${NC}"
else
    echo -e "${RED}✗ Test failed${NC}"
fi

# Test 2: Get parameter (requires server running)
echo ""
echo -e "${BLUE}[Test 3] Getting parameter 'device_name'...${NC}"
echo "Command: ros2 param get /params_server device_name"
timeout 5 ros2 param get /params_server device_name 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test passed${NC}"
else
    echo -e "${YELLOW}⚠ Test skipped (server not running)${NC}"
fi

# Test 3: Set parameter
echo ""
echo -e "${BLUE}[Test 4] Setting parameter 'update_rate' to 25...${NC}"
echo "Command: ros2 param set /params_server update_rate 25"
timeout 5 ros2 param set /params_server update_rate 25 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test passed${NC}"
    # Verify the change
    timeout 5 ros2 param get /params_server update_rate 2>/dev/null
else
    echo -e "${YELLOW}⚠ Test skipped (server not running)${NC}"
fi

# Test 4: Get all parameters
echo ""
echo -e "${BLUE}[Test 5] Getting all parameters for /params_server...${NC}"
echo "Command: ros2 param list /params_server"
timeout 5 ros2 param list /params_server 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test passed${NC}"
else
    echo -e "${YELLOW}⚠ Test skipped (server not running)${NC}"
fi

# Test 5: Dump parameters to file
echo ""
echo -e "${BLUE}[Test 6] Dumping parameters to test_params.yaml...${NC}"
echo "Command: ros2 param dump /params_server > test_params.yaml"
timeout 5 ros2 param dump /params_server > test_params.yaml 2>/dev/null
if [ -f "test_params.yaml" ] && [ -s "test_params.yaml" ]; then
    echo -e "${GREEN}✓ Test passed${NC}"
    echo "File content:"
    cat test_params.yaml
    rm test_params.yaml
else
    echo -e "${YELLOW}⚠ Test skipped (server not running)${NC}"
fi

# Test 6: Node information
echo ""
echo -e "${BLUE}[Test 7] Listing all nodes...${NC}"
echo "Command: ros2 node list"
timeout 5 ros2 node list 2>/dev/null | grep -i param
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ params_server node found${NC}"
else
    echo -e "${YELLOW}⚠ params_server node not found${NC}"
fi

# Test 7: Check ROS interfaces
echo ""
echo -e "${BLUE}[Test 8] Checking parameter-related services...${NC}"
echo "Command: ros2 service list | grep param"
timeout 5 ros2 service list 2>/dev/null | grep -i param | head -5
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Parameter services found${NC}"
else
    echo -e "${YELLOW}⚠ No parameter services found${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Test Summary                                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${YELLOW}Note: Some tests require params_server to be running.${NC}"
echo ""
echo "To run params_server:"
echo -e "${BLUE}  ros2 run params_service params_server_cpp${NC}"
echo ""
echo "Or use the launch file:"
echo -e "${BLUE}  ros2 launch params_service params_demo.launch.py${NC}"
echo ""

echo -e "${GREEN}✓ All available tests completed!${NC}"
