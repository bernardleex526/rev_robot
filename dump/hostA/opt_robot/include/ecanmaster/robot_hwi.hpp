///
/// @file robot_hwi.hpp
/// @author vcb (www.deeprobotics.cn)
/// @brief 
/// @version 0.1
/// @date 2024-12-16
/// 
/// @copyright Copyright (c) 2024
/// 
///


#ifndef _ROBOT_HWI_H_
#define _ROBOT_HWI_H_
#include <map>
#include <iostream>
#include <string>
#include "types/data_structures.h"

// RobotConfig 类，用于封装模型选择和关节信息读取逻辑
using namespace ecan;
class RobotConfig {
public:
  RobotConfig();
  std::string getModel(void);
  bool getTypeForModel(const std::string& model);
  std::map<std::uint8_t, XYZ> getMapForModel(const std::string& model);
};

#endif // _ROBOT_HWI_H_