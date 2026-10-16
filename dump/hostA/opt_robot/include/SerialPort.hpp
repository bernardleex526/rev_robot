#ifndef SERIALPORT_HPP
#define SERIALPORT_HPP

#include <string>
#include <termios.h>
#include <cstddef>

// SerialPort.hpp
class SerialPort {
public:
    // 构造函数和析构函数
    SerialPort(const std::string& device);
    ~SerialPort();

    // 打开和关闭串口
    bool open();
    void close();

    // 配置串口
    bool configurePort();
    bool setBaudRate(speed_t baudRate);
    bool setDataBits(int dataBits);
    bool setStopBits(int stopBits);
    bool setParity(bool enableParity, bool oddParity);
    bool setRecvOvertime(int timeoutSeconds, int timeoutInterval);
    bool disableCanonicalMode();
    bool setFlowControl(bool enableHardwareFlowControl, bool enableSoftwareFlowControl);
    bool setNonBlocking();
    void clearInputBuffer(void);
    void clearOutputBuffer(void);

    // 数据读写
    ssize_t write(const void* buf, size_t len);
    ssize_t read(void* buf, size_t len);
    ssize_t readNonBlocking(void* buf, size_t len, int timeoutSeconds);

    // 获取当前配置
    std::string getCurrentConfiguration();

    std::string getCurrentDeviceName();
    

private:
    int fd;
    std::string deviceName;
    struct termios tty;
};





#endif // SERIALPORT_HPP
