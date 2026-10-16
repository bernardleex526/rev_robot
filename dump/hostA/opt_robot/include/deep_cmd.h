/*
 * @Date : 2024-10-02 11:22:24
 * @LastEditors : m-sharp moxiaobo0571@163.com
 * @LastEditTime : 2024-10-12 14:06:24
 * @FilePath : /CB1/SensorHub/mcu_control/inc/deep_cmd.h
 * @brief :
 *
 * Copyright (c) 2024 by DeepRobotics.cn, All Rights Reserved.
 */
#pragma once

#include <stdint.h>

/**
 * @brief 接收外部控制命令
 */
enum ServiceCode
{
  kCodeQueryStatus = 0, ///< 状态查询
  kCodeNeckMotor   = 1, ///< 颈电机控制
  kCodeLight       = 2, ///< 调节灯光
  /// @todo kCodeLight考虑根据sensor hub的控制方式进行code及拆分.
};

enum LightType
{
  kLightEye   = 2, ///< 眼灯
  kLightFlash = 3, ///< 照明灯
  kLightTail  = 4, ///< 尾灯

};

enum LightPresetMethod
{
  kLightEyeON      = 0x020001, ///< 0x020001 眼灯常亮,默认 #00FF00
  kLightEyeOff     = 0x020002, ///< 0x020002 眼灯关闭,
  kLightEyeBreath  = 0x020003, ///< 0x020003 眼灯呼吸,默认3秒渐灭,3秒渐明
  kLightEyeTwinkle = 0x020004, ///< 0x020004 眼灯闪烁,默认明?秒,灭0.1秒

  kLightFlashOn  = 0x030001, ///< 0x030001
  kLightFlashOff = 0x030002, ///< 0x030002

  kLightTailA0 = 0x040A00, ///< 0x040A00 自定义
  // 预设呼吸型
  kLightTailWhiteBrtheSlow  = 0x040A01, ///< 0x040A01 白色慢
  kLightTailWhiteBrtheMidle = 0x040A02, ///< 0x040A02 白色中
  kLightTailWhiteBrtheFast  = 0x040A03, ///< 0x040A03 白色快
  kLightTailCyanBrtheSlow   = 0x040A04, ///< 0x040A04 青色慢

  kLightTailB0 = 0x040B00, ///<  0x040B00 自定义
  // 预设闪烁型
  kLightTailCyanFlash   = 0x040B01, ///<  0x040B01 青色闪烁
  kLightTailWhiteFlash  = 0x040B02, ///<  0x040B02 白色闪烁
  kLightTailRedFlash    = 0x040B03, ///<  0x040B03 红色闪烁
  kLightTailRedYewFlash = 0x040B04, ///<  0x040B04 红黄交替闪烁
  kLightTailB5          = 0x040B05, ///<  0x040B04 黄色闪烁，4HZ

  kLightTailC0 = 0x040C00, ///< 0x040C00 自定义
  // 预设常亮型LightParam
  kLightTailCyan  = 0x040C01, ///< 0x040C01 青色常亮
  kLightTailWhite = 0x040C02, ///< 0x040C02 白色常亮
  kLightTailRed   = 0x040C03, ///< 0x040C03 红色常亮

  kLightTailD0 = 0x040D00, ///< 0x040D00 自定义
  // 预设流水型
  kLightTailCyanFlow  = 0x040D01, ///< 0x040D01 青色流水
  kLightTailColorFlow = 0x040D02, ///< 0x040D02 彩色流水

  kLightTailF0 = 0x040F00, ///< 0x040F00 自定义
  // 预设特殊型
  kLightTailF1 = 0x040F01, ///< 0x040F01 替换当前颜色1为黄色 1111
};

#pragma pack(push, 1)
struct FrameHead
{
  uint32_t size;         // 报文长度
  uint32_t code;         // 命令码
  uint32_t state;        // 预留
  uint32_t timestamp_ns; // 预留
  uint32_t frame_id;     // 预留
}; // 协议头

struct UltrasonicData // mm
{
  uint32_t distance_front;
  uint32_t distance_back;
};

struct TouchData // ms
{
  uint32_t touch_left;
  uint32_t elapse_left;
  uint32_t touch_right;
  uint32_t elapse_right;
  uint32_t touch_jaw;
  uint32_t elapse_jaw;
};

/**
 * @brief 灯控的参数
 * method 分成自定义类型与预设类型,预设类型见 enum LightPresetMethod
 * |   方式     | 无效值  |   常亮  |     闪烁    |     呼吸     |    流水     |
 * | :-------: | :----: | ------- | :--------: | :---------: | :--------: |
 * | lightness |        | 最高亮度 |   最高亮度   |   最高亮度   |  最高亮度   |
 * |  color1   |   0    | 使用颜色 |  使用颜色1   |  使用颜色1   |  使用颜色1  |
 * |  color2   |   0    |   值0   | 0/使用颜色2  | 0/使用颜色2  | 0/使用颜色2 |
 * |   time1   |   0    |   值0   | 持续亮的时间  |  渐灭的时间  |            |
 * |   time2   |   0    |   值0   | 持续灭的时间  | 0/渐亮的时间 |            |
 * |  cycles   |   0    |   值0   |   循环次数   |   循环次数   |  循环次数   |
 */
struct LightParam
{
  uint32_t method;    // 亮灯的方式 ： 常亮、闪烁、呼吸、流水灯
  uint32_t lightness; // 亮度 0-100
  uint32_t color1;    //
  uint32_t color2;    //
  uint32_t time1;     // ms
  uint32_t time2;     // ms
  uint32_t cycles;    // 次数
};

struct NeckParam
{
  uint32_t angle; // 转动量[0, 1000] 500居中，0狗头最左，1000狗头最右
};

struct FrameBodyRequest
{
  union
  {
    LightParam light;
    NeckParam  neck;
  };
};
struct FrameBodyRespond
{
  UltrasonicData ultrasonic;
  NeckParam      neck;
  TouchData      touch;
  LightParam     eye;
  LightParam     tail;
  LightParam     flash;
};

struct Frame
{
  FrameHead head;
  union
  {
    FrameBodyRequest rqt_body;
    FrameBodyRespond rsp_body;
  };
};
#pragma pack(pop)