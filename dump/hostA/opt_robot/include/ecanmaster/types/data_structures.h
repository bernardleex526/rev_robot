///
/// @file data_structures.h
/// @author vcb (www.deeprobotics.cn)
/// @brief 
/// @version 0.1
/// @date 2024-04-29
/// 
/// @copyright Copyright (c) 2024
/// 
///
#include <stdint.h>
#ifndef STRUCT_TYPEDEF_H
#define STRUCT_TYPEDEF_H
namespace ecan{
const uint32_t kCanChannelNumMax = 4;
const uint32_t kSingleJointNumMax = 7;
const uint32_t kSDKRunCPUIndex = 5;

#pragma pack(2)
struct ImuData{
  uint32_t timestamp;
  union{
    float buffer_float[9];
    uint8_t buffer_byte[3][12];
    struct{
      float roll, pitch, yaw;
      float omega_x, omega_y, omega_z;
      float acc_x, acc_y, acc_z;
    };
  };
};
// 命令索引
enum CommandIndex{
  kIndexDisable = 1,
  kIndexEnable = 2,
  kIndexCalibration = 3,
//    kIndexOutEncoderCalibration = 4,
  kIndexMotorControl = 4,
  kIndexMotorReset = 5,
  kIndexSetHome = 6,
  kIndexSetGear = 7,
  kIndexSetID = 8,
  kIndexSetCanTimeout = 9,
  kIndexSetBandwidth = 10,
  kIndexSetLimitCurrent = 11,
  kIndexSetUnderVoltage = 12,
  kIndexSetOverVoltage = 13,
  kIndexSetMotorTemperature = 14,
  kIndexSetDriverTemperature = 15,
  kIndexSaveConfig = 16,
  kIndexErrorReset = 17,
  kIndexWriteAppBackStart = 18,
  kIndexWriteAppBack = 19,
  kIndexCheckAppBack = 20,
  kIndexDfuStart = 21,
  kIndexGetVersion = 22,
  kIndexGetStatusWord = 23,
  kIndexGetConfig = 24,
  kIndexOutEncoderCalibration = 25,
  kIndexGetOutEncoder = 26,
  kIndexCalibReport = 31
};
#define BATTERY_SERIAL_NUM_LENTH  32
typedef struct{      // BatterySensorData  BatteryBaseInfoTag
  uint16_t voltage;             ///<总电压            单位10mV
  int16_t  current;             ///<总电流            单位10mA
  uint16_t remaining_capacity;  ///<剩余容量          单位10mAH
  uint16_t nominal_capacity;    ///<标称容量          单位10mAH
  uint16_t cycles;              ///<循环次数
  uint16_t production_date;     ///<生产日期
  uint16_t balanced_low;        ///<均衡低
  uint16_t balanced_high;       ///<均衡高
  uint16_t protected_state;     ///<保护状态

  uint8_t software_version;  ///<软件版本
  uint8_t battery_level;     ///<剩余容量百分比
  uint8_t mos_state;         ///<Mos状态W
  uint8_t battery_quantity;  ///<电池串数
  uint8_t battery_ntc;       ///<NTC个数

  float battery_temperature[4];
  char serial_num[BATTERY_SERIAL_NUM_LENTH];
  uint16_t cell_voltage[20];  // 0x04返回的单体电压数组
  uint16_t ch_plus_mV;      /* ch+：单位10mV，高位在前 */
  uint8_t  ch_det;          /* ch_det：充电检测IO口状态 */
  uint8_t  bat_resp_code;    /* 电池响应状态码：0x00操作成功；0x80命令码不存在；0x81操作错误无效操作；0x82校验错误；0x83密码操作时密码配对错误 */

  uint8_t res1[140];          //预留共占用256字节
}BatterySensorData;
typedef struct {
  float pos;
  float vel;
  float tor;
  
  union {
    int16_t motor_temp;
    int16_t kp;
  };
  union {
    int16_t driver_temp;
    int16_t kd;
  };
} JointUnitData;

typedef union {
  struct{
    uint8_t board_id;
    uint8_t can_ch;
    uint16_t can_id;
  };
  uint32_t xyz;
}XYZ;

const int kJointCount = 32;//最大关节数量

typedef struct {
  XYZ board_info;
  union{
    JointUnitData joint_data;
    uint8_t buffer[sizeof(JointUnitData)];
  };
  union {
    uint16_t status_word;
    uint16_t control_word;
  };
  uint16_t data_id;
} JointUnit;

typedef JointUnit JointRawData[kJointCount];
typedef BatterySensorData BatteryInfo[2];
typedef struct 
{
    uint8_t hard_stop;
    uint8_t imu_status;
    uint8_t res[254];
} ECAN_STATUS;

#pragma pack()
};
#endif 
