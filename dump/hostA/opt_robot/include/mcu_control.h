#ifndef _HOST_SYS_H
#define _HOST_SYS_H


#include <iostream>
#include <cstring>
#include <unistd.h>  // 包含sleep() 和 usleep()
#include <vector>
#include <queue>
#include <chrono>
#include <mutex>
#include <condition_variable>
#include <variant>


#include "SerialPort.hpp"
#include "mcu_protocolstack.h"

std::string getFileNameFromPath(const std::string& filepath);
void delay(unsigned milliseconds);



class mcu_ProtocolStack;  // 前向声明

class mcu_Control{
    public:
    #define REALTIME_LIMIT 200
        // mcu_Control(std::string device="/dev/ttyS1");
        mcu_Control(std::string device="/dev/ttyS3");
        ~mcu_Control();


        
        void mcuReset(void);
        uint8_t getCurrentSector(void); // 1:bootloader 2:app
        std::string getSoftwareVer(void); //返回字符串代表单片机固定版本
        void jump2sector(void); //boot/app之间相互跳转
        void mcuFmUpdate(const std::string& filepath = "./app.bin"); //必须为bin文件
        void mcuBootFmUpdate(const std::string& filepath = "./boot.bin"); //必须为bin文件  


         /**
         * @brief 控制灯光效果的函数
         * 
         * 该函数用于控制不同类型的灯光效果。
         * 
         * @param mode
         *     - 1: 常亮
         *     - 2: 闪烁
         *     - 3: 呼吸
         *     - 4: 单灯珠流水灯
         *     - 5: 四灯珠流水灯
         *     - 6: 红黄交替
         *     - 7: 黄色替换
         * @brief 1/2/3通用，即尾灯/眼灯都响应
         *        4/5/6/7，只有尾灯响应
         * 
         * 
         * 
         * @param duty 
         * @brief 单位：ms
         * 
         * 
         * @param brg
         * @brief 32位整数，格式为0x00BBRRGG
         **/

        void CB1_V3_LEDcontrol(uint8_t mode, uint32_t brg, uint16_t duty);

        /**
         * @brief 用作尾灯接在F1的硬件适配接口
         * 
         * 该函数用于控制尾灯不同类型的灯光效果。
         * 
         * @param mode
         *     - 1: 常亮
         *     - 2: 闪烁
         *     - 3: 呼吸
         *     - 4: 单灯珠流水灯
         *     - 5: 四灯珠流水灯
         *     - 6: 红黄交替
         *     - 7: 黄色替换
         * 
         * @param duty 
         * @brief 单位：ms
         * 
         * 
         * @param brg
         * @brief 32位整数，格式为0x00BBRRGG
         **/

        void CB1_V3_LIGHTcontrol(uint32_t duty);
        //该函数用于控制照明灯灯不同占空比的亮度，占空比通过duty（范围0-100）参数控制。

        void CB1_V2_TailLight(uint8_t tail_mode, uint32_t tail_rgb, uint16_t duty);  

        //打开胸灯， 1：打开 2：关闭
        void CB1_V3_FlashLight(uint8_t mode);

        /**
         * @brief 眨眼实现
         * 
         * @param duty 
         * @brief 单位：ms
         * 
         **/
        void CB1Eyeblink(uint16_t duty);

        /**
         * @brief 颈电机控制
         * 
         * @param data 
         * @brief 数值范围 0-2000，1000为狗头居中位置
         * 
         **/
        void setGearMotor(uint16_t data);

        
        /**
         * @brief 用作胸灯亮度可调节的硬件版本
         * 
         * @param data 
         * @brief 百分比 0-100%
         * 
         **/

        void setFloodLight(uint16_t data); 
        
        /**
         * @brief 超声数据获取
         * 
         * @return 
         * @brief 单位：mm，两个值分别代表前后
         * 
         **/

        std::vector<uint16_t> getUltraSonicDistance();

        /**
         * @brief 触摸检测
         *
         * @param state 
         * @brief state后三位代表触摸状态，1.检测到触摸状态 0.无触摸状态
         * 
         * 
         * @return 
         * @brief 返回值代表是否在200ms内检测到，true代表200ms以内，false代表200ms以外
         * 
        **/
        bool getTouchState(uint8_t &state);

        /**
         * @brief 连续不间断查询版本，检验单片机固件是否会奔溃
         *
         * @param conut 
         * @brief 连续指令次数
         * 
         * 
         * @return None
         * 
        **/
        void StressTest(uint32_t conut);


        
        

    private:
        class Impl;              // 前向声明内部实现类
        Impl* pImpl;             // 指向实现类的指针
        bool is_realtime(STEADY_CLOCK time);

};
//cb1 专用灯效类

#endif


