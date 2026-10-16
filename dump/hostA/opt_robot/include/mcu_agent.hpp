/*
 * @Date : 2024-10-12 12:40:19
 * @LastEditors : m-sharp moxiaobo0571@163.com
 * @LastEditTime : 2024-10-12 14:18:05
 * @FilePath : /CB1/SensorHub/mcu_control/inc/mcu_agent.hpp
 * @brief :
 *
 * Copyright (c) 2024 by DeepRobotics.cn, All Rights Reserved.
 */
#pragma once
#include <unistd.h> // 包含sleep() 和 usleep()

#include <cstdint>
#include <cstring>
#include <iostream>
#include <sstream>
#include <mutex>
#include <chrono>

#include "deep_cmd.h"
#include "mcu_control.h"
#pragma pack(push, 1)
struct LightParamV0
{
  uint8_t  mode;   ///< 模式(1.呼吸 2.闪烁 3.常亮 4.流水灯 5.交叉 6.关闭)
  uint16_t period; ///< 单次循环周期(0-65535ms)
  uint32_t color;  ///< 0x00RRGGBB
  LightParamV0() : mode(0), period(0), color(0) {}
};
#pragma pack(pop)

// #define Hardware_v2
#ifndef Hardware_v2
class McuAgent
{
  private:
      static McuAgent *instance;
      LightParamV0     eye_param_;
      LightParamV0     flash_param_;
      LightParamV0     tail_param_;
      uint32_t         duration_ms_;
      // McuAgent(/* args */) : head_mcu_control_(mcu_Control("/dev/ttyS3")) {}
      McuAgent()
          // : head_mcu_control_("/dev/ttyS1"),
      //     //   tail_mcu_control_("/dev/ttyS7"),
          : head_mcu_control_("/dev/ttyS3"),
            duration_ms_(500)
      {
      }
      bool isActionTimeFellShort(std::chrono::steady_clock::time_point lastRecvTime)
      {
        auto now = std::chrono::steady_clock::now();
        auto elapsed_ms =
            std::chrono::duration_cast<std::chrono::milliseconds>(now - lastRecvTime).count();
        return elapsed_ms <= duration_ms_;
      }

  public:
  mcu_Control head_mcu_control_;
  // mcu_Control tail_mcu_control_;
  static McuAgent &Instance()
  {
    static std::once_flag initFlag;
    std::call_once(initFlag, []() { instance = new McuAgent(); });
    return *instance;
  };

  /// 禁用传值构造和右值构造函数
  McuAgent(const McuAgent &)            = delete;
  McuAgent(const McuAgent &&)           = delete;
  McuAgent &operator=(const McuAgent &) = delete;

  void McuReset(int mode = 1) {
    if(mode == 1){
      head_mcu_control_.mcuReset();
    } 
    // else if(mode == 2){
    //   tail_mcu_control_.mcuReset();
    // } 
    
  }

  void McuUpgrade(int mode = 1) {
    if(mode == 1){
      head_mcu_control_.mcuFmUpdate(); 
    } 
    // else if(mode == 2){
    //   tail_mcu_control_.mcuFmUpdate(); 
    // } 
  }

  std::vector<uint16_t> GetUltralsonicData() {
    return head_mcu_control_.getUltraSonicDistance();
  }

  uint8_t GetTouchData()
  {
    uint8_t data;
    if (head_mcu_control_.getTouchState(data)) {
      return data;
    } else {
      return static_cast<uint8_t>(-1);
    }
  }

  void SetNeckData(uint16_t _angle)
  {
    static int16_t lastAngle = 1001;
    if (_angle > 2000) {
      std::cout << "输入超出范围" << std::endl;
      return;
    }
    if (lastAngle != _angle) {
      head_mcu_control_.setGearMotor(_angle);
      lastAngle = _angle;
      // std::cout << "设置舵机角度" << std::endl;
    }
  }

  /**
   * @brief
   * @param {uint8_t} _mode
   * @return {*}
   */
  void PresetFlashLight(uint32_t _mode = kLightFlashOn)
  {
    bool is_valid = true;
    static uint32_t last     = 0;
    switch (_mode) {
      case kLightFlashOn: flash_param_.mode = 1; break;
      case kLightFlashOff: flash_param_.mode = 2; break;
      default: is_valid = false; break;
    }
    if (is_valid == true && last != _mode) {
      head_mcu_control_.CB1_V3_FlashLight(flash_param_.mode);
    }
    last = _mode;
  }

  /**
   * @brief 根据预设类型控制眼灯
   * @param {uint8_t} _type
   * @return {*}
   */
  void PresetEyeLight(uint32_t _type = kLightEyeON, uint16_t durationTime = 100)
  {
    bool is_valid = true;
    static uint32_t last     = 0;
    switch (_type) {
      case kLightEyeON:
        eye_param_.mode   = 1;
        eye_param_.period = 1;
        eye_param_.color  = 0xFF00E0;
        break;
      case kLightEyeOff:
        eye_param_.mode   = 1;
        eye_param_.period = 1;
        eye_param_.color  = 0x000000;
        break;
      case kLightEyeBreath:
        eye_param_.mode   = 3;
        eye_param_.period = 3000;
        eye_param_.color  = 0xFF00E0;
        break;
      case kLightEyeTwinkle:
        eye_param_.mode   = 4;
        eye_param_.period = durationTime;
        eye_param_.color  = 0xFF00E0;
        break;
      default: is_valid = false; break;
    }
    if (is_valid == true && (last != _type || _type == kLightEyeTwinkle)) {
      if(eye_param_.mode != 4){
        head_mcu_control_.CB1_V3_LEDcontrol(eye_param_.mode,  eye_param_.color,eye_param_.period);
      }
      else{
        head_mcu_control_.CB1Eyeblink(eye_param_.period);
      }
    }
    last = _type;
  }

  /**
   * @brief 根据预设类型控制尾灯,颜色通道 B R G
   * @param {uint8_t} _type 尾灯的预置类型1.呼吸 2.闪烁 3.常亮 4.流水灯 5.交叉
   * @return {*}
   */
  void PresetTailLight(uint32_t _type = kLightTailColorFlow)
  {
    bool is_valid = true;
    static uint32_t last     = 0;
    switch (_type) {
      //呼吸
      case kLightTailWhiteBrtheSlow:
        tail_param_.mode   = 3;
        tail_param_.period = 3000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailWhiteBrtheMidle:
        tail_param_.mode   = 3;
        tail_param_.period = 2000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailWhiteBrtheFast:
        tail_param_.mode   = 3;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailCyanBrtheSlow:
        tail_param_.mode   = 3;
        tail_param_.period = 3000;
        tail_param_.color  = 0xFF00FF;
        break;
      //闪烁
      case kLightTailCyanFlash:
        tail_param_.mode   = 2;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFF00FF;
        break;
      case kLightTailWhiteFlash:
        tail_param_.mode   = 2;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailRedFlash:
        tail_param_.mode   = 2;
        tail_param_.period = 1000;
        tail_param_.color  = 0x00FF00;
        break;
      case kLightTailRedYewFlash:
        tail_param_.mode   = 6;
        tail_param_.period = 1000;
        tail_param_.color  = 0;
        break;
      case kLightTailB5:
        tail_param_.mode   = 2;
        tail_param_.period = 1000;
        tail_param_.color  = 0xffff00;
        break;
      //常亮
      case kLightTailCyan:
        tail_param_.mode   = 1;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFF00E0;
        break;
      case kLightTailWhite:
        tail_param_.mode   = 1;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailRed:
        tail_param_.mode   = 1;
        tail_param_.period = 1000;
        tail_param_.color  = 0x00FF00;
        break;
      
      //流水
      case kLightTailCyanFlow:
        tail_param_.mode   = 4;
        tail_param_.period = 2000;
        tail_param_.color  = 0xFF00E0;
        break;
      case kLightTailColorFlow:
        tail_param_.mode   = 5;
        tail_param_.period = 1000;
        tail_param_.color  = 0x00FF00;
        break;
      case kLightTailF1: 
        tail_param_.mode   = 6;
        tail_param_.color  = 0xFFFF00;
        tail_param_.period = 5;
        break;

      default: is_valid = false; break;
    }
    // if (is_valid == true && last != _type) {
    //   tail_mcu_control_.CB1_V3_LEDcontrol(tail_param_.mode,  tail_param_.color ,tail_param_.period);
    // }
    last = _type;
  }

  void Tail(uint32_t _type = kLightTailColorFlow) { PresetTailLight(_type); }
  void Eye(uint32_t _type = kLightEyeON) { PresetEyeLight(_type); }

  std::string McuVersion(int mode = 1)
  {
    if(mode == 1){
      return head_mcu_control_.getSoftwareVer(); 
    } 
    // else if(mode == 2){
    //   return tail_mcu_control_.getSoftwareVer(); 
    // } 
    return " ";
  }

  ~McuAgent(){};
};


#else


class McuAgent
{
  private:

  LightParamV0 eye_param_;
  LightParamV0 flash_param_;
  LightParamV0 tail_param_;
  // McuAgent(/* args */) : mcu_control_(mcu_Control("/dev/ttyS1")) {};
  McuAgent(/* args */) : mcu_control_(mcu_Control("/dev/ttyS3")) {};

  public:
  mcu_Control mcu_control_;
  static McuAgent &Instance()
  {
    static McuAgent ma;
    return ma;
  };

  /// 禁用传值构造和右值构造函数
  McuAgent(const McuAgent &)            = delete;
  McuAgent(const McuAgent &&)           = delete;
  McuAgent &operator=(const McuAgent &) = delete;

  void McuReset() { mcu_control_.mcuReset(); }

  void McuUpgrade() { mcu_control_.mcuFmUpdate(); }

  std::vector<uint16_t> GetUltralsonicData() { return mcu_control_.getUltraSonicDistance(); }

  uint8_t GetTouchData()
  {
    uint8_t data;
    mcu_control_.getTouchState(data);
    return data;
  }

  void SetNeckData(uint16_t _angle)
  {
    if (_angle > 2000) {
      std::cout << "输入超出范围" << std::endl;
      return;
    }
    mcu_control_.setGearMotor(_angle);
    return;
  }

  /**
   * @brief
   * @param {uint8_t} _mode
   * @return {*}
   */
  void PresetFlashLight(uint32_t _mode = kLightFlashOn)
  {
    bool is_valid = true;
    switch (_mode) {
      case kLightFlashOn: flash_param_.mode = 1; break;
      case kLightFlashOff: flash_param_.mode = 2; break;
      default: is_valid = false; break;
    }
    if (is_valid == true) {
      mcu_control_.CB1LightControl(0, 0, flash_param_.mode, 0, 0, 0, 0);
    }
  }

  /**
   * @brief 根据预设类型控制眼灯
   * @param {uint8_t} _type
   * @return {*}
   */
  void PresetEyeLight(uint32_t _type = kLightEyeON)
  {
    bool is_valid = true;

    switch (_type) {
      case kLightEyeON:
        eye_param_.mode   = 1;
        eye_param_.period = 1;
        eye_param_.color  = 0x00FFE0;
        break;
      case kLightEyeOff:
        eye_param_.mode   = 2;
        eye_param_.period = 1;
        eye_param_.color  = 0x00FFE0;
        break;
      case kLightEyeBreath:
        eye_param_.mode   = 3;
        eye_param_.period = 3000;
        eye_param_.color  = 0x00FFE0;
        break;
      case kLightEyeTwinkle:
        eye_param_.mode   = 4;
        eye_param_.period = 100;
        eye_param_.color  = 0x00FFE0;
        break;
      default: is_valid = false; break;
    }
    if (is_valid == true) {
      mcu_control_.CB1LightControl(eye_param_.mode, 0, 0, eye_param_.period, 0, eye_param_.color,
                                   0);
    }
  }

  /**
   * @brief 根据预设类型控制尾灯
   * @param {uint8_t} _type 尾灯的预置类型1.呼吸 2.闪烁 3.常亮 4.流水灯 5.交叉
   * @return {*}
   */
  void PresetTailLight(uint32_t _type = kLightTailColorFlow)
  {
    bool is_valid = true;

    switch (_type) {
      case kLightTailWhiteBrtheSlow:
        tail_param_.mode   = 1;
        tail_param_.period = 3000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailWhiteBrtheMidle:
        tail_param_.mode   = 1;
        tail_param_.period = 2000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailWhiteBrtheFast:
        tail_param_.mode   = 1;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailCyanFlash:
        tail_param_.mode   = 2;
        tail_param_.period = 1000;
        tail_param_.color  = 0x00FFE0;
        break;
      case kLightTailWhiteFlash:
        tail_param_.mode   = 2;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailRedFlash:
        tail_param_.mode   = 2;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFF0000;
        break;
      case kLightTailRedYewFlash:
        tail_param_.mode   = 5;
        tail_param_.period = 4000;
        tail_param_.color  = 0;
        break;
      case kLightTailB5:
        tail_param_.mode   = 2;
        tail_param_.period = 250;
        tail_param_.color  = 0xffe400;
        break;
      case kLightTailCyan:
        tail_param_.mode   = 3;
        tail_param_.period = 1000;
        tail_param_.color  = 0x00FFE0;
        break;
      case kLightTailWhite:
        tail_param_.mode   = 3;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFFFFFF;
        break;
      case kLightTailRed:
        tail_param_.mode   = 3;
        tail_param_.period = 1000;
        tail_param_.color  = 0xFF0000;
        break;
      case kLightTailCyanFlow:
        tail_param_.mode   = 4;
        tail_param_.period = 2000;
        tail_param_.color  = 0x00FFE0;
        break;
      case kLightTailColorFlow:
        tail_param_.mode   = 6;
        tail_param_.period = 1000;
        tail_param_.color  = 0x00FF00;
        break;
      case kLightTailF1: 
        tail_param_.color = 0xFFFF00; 
        tail_param_.period = 1;
        tail_param_.mode   = 7;
        break;

      default: is_valid = false; break;
    }
    if (is_valid == true) {
      mcu_control_.CB1LightControl(0, tail_param_.mode, 0, 0, tail_param_.period, 0,
                                   tail_param_.color);
    }
  }

  void Tail(uint32_t _type = kLightTailColorFlow) { PresetTailLight(_type); }
  void Eye(uint32_t _type = kLightEyeON) { PresetEyeLight(_type); }

  std::string McuVersion() { return mcu_control_.getSoftwareVer(); }

  ~McuAgent(){};
};

#endif

