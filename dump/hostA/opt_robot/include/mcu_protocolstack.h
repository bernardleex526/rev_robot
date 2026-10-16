#ifndef _MCU_PROTOSTACK_H
#define _MCU_PROTOSTACK_H


#include "common_lib.h"

#include "SerialPort.hpp"




std::string toHexString(const uint8_t* byteArray, size_t length);
void print_time_point(const std::chrono::time_point<std::chrono::steady_clock>& time_point);

// 定义一个结构体或枚举类型，用于表示不同的功能码
enum FuncCode {
    NO_RESPONSE_REQUEST = 0x15, // 无响应请求
    ACK_REQUEST = 0x16,          // 有ACK请求
    RESPONSE_WITH_CONTENT = 0x17, // 要求回复携带内容
    RESPONSE_FRAME = 0x21        // 应答帧，根据数据长度确定是否带数据内容
};

typedef struct{
    uint8_t header[2];
    uint8_t frame_id;
    uint8_t version;
    uint8_t type;
    uint8_t func_code;
    uint16_t size;
    uint16_t crc16;
}frameHeader_t;

typedef struct QueryStruct{
    uint8_t data[1024];
    uint16_t size;
    std::chrono::time_point<std::chrono::steady_clock> current_time;
}querystruct_t;

#define STEADY_CLOCK std::chrono::time_point<std::chrono::steady_clock>

class mcu_ProtocolStack{
    public:
    
    
        // mcu_ProtocolStack(std::string device="/dev/ttyS1");
        mcu_ProtocolStack(std::string device="/dev/ttyS3");
        ~mcu_ProtocolStack();
               
        uint8_t sendData(FuncCode frame_type, uint8_t func_code, uint16_t len, uint8_t *dat);
        bool is_reply_ack(uint8_t func_code, querystruct_t &temp);
        bool is_reply_ack(uint8_t frame_id, uint8_t func_code, querystruct_t &temp );
        
        bool is_reply_data(uint8_t func_code, querystruct_t &temp);
        bool is_reply_data(uint8_t frame_id,uint8_t func_code, querystruct_t &temp);

        bool is_data_request(uint8_t frame_id, uint8_t func_code, querystruct_t &temp);
        bool is_noack_data_request(uint8_t func_code, querystruct_t &temp);
        STEADY_CLOCK getProgramRunTime();  

        void print_ack_notify_struct_queue(); 
        void print_reply_data_notify_queue(); 
        void print_data_request_notify_struct_queue(); 
        void print_noack_request_notify_struct_queue(); 

        



    
    private:
//帧长度    
    #define RXBUFFERLEN 255
    #define CQBUFFERLEN 300

    #define HEADER_LEN 255

//帧结构
    // #define FRAME_HEAD 0x44,0x52
    #define FRAME_HEAD 0xEE,0xEF
    #define FRAME_ID_BIAS 2
    #define FRAME_VERSION_BIAS 3
    #define FRAME_TYPE 4
    #define FRAME_FUNC_CODE 5
    #define FRAME_DATA_SIZE_BIAS 6
    #define FRAME_CRC_BIAS 8
    #define FRAME_DATA_BIAS 10

        typedef struct frame_mgt
        {
            uint8_t frame_id;
            uint8_t func_code;
            uint8_t *data;
            uint8_t *reply_data;
            std::chrono::time_point<std::chrono::steady_clock> current_time ;

        }frame_mgt_t;

        

        typedef struct ack_notify_struct
        {
            uint8_t func_code;
            uint8_t frame_id;
            std::chrono::time_point<std::chrono::steady_clock> current_time ;
        }ack_notify_struct_t;

        typedef struct reply_data_notify_struct
        {
            uint8_t func_code;
            uint8_t frame_id;
            uint8_t *notify_queue;
            uint16_t notify_queue_size;
            std::chrono::time_point<std::chrono::steady_clock> current_time ;
        }reply_data_notify_t;

        typedef struct ack_request_notify_struct
        {
            uint8_t func_code;
            uint8_t *notify_queue;
            uint16_t notify_queue_size;
            std::chrono::time_point<std::chrono::steady_clock> current_time ;
        }ack_request_notify_struct_t;

        typedef struct noack_request_notify_struct
        {
            uint8_t func_code;
            uint8_t *notify_queue;
            uint16_t notify_queue_size;
            std::chrono::time_point<std::chrono::steady_clock> current_time ;
        }noack_request_notify_struct_t;

        typedef struct data_request_notify_struct
        {
            uint8_t func_code;
            uint8_t frame_id;
            uint8_t *notify_queue;
            uint16_t notify_queue_size;
            std::chrono::time_point<std::chrono::steady_clock> current_time ;
        }data_request_notify_struct_t;


        std::vector<ack_notify_struct_t> ack_notify_struct_queue;
        std::vector<reply_data_notify_t> reply_data_notify_queue;

        
        std::vector<data_request_notify_struct_t> data_request_notify_struct_queue;
        std::vector<ack_request_notify_struct_t> ack_request_notify_struct_queue;
        std::vector<noack_request_notify_struct_t> noack_request_notify_struct_queue;

        const size_t max_queue_size = 10; // 队列长度限制
        std::mutex ack_mtx,reply_data_mtx,data_request_mtx,noack_request_mtx, ack_request_mtx;

        std::vector<frame_mgt_t> tx_frame_queue;
        std::vector<frame_mgt_t> rx_frame_queue;


        uint8_t rxbuffer[RXBUFFERLEN];
        uint8_t cqbuffer[CQBUFFERLEN];


        SerialPort *serial;

 
        std::chrono::time_point<std::chrono::steady_clock> program_start_time;

        // std::deque<uint8_t> serialDataQueue; // 用于存储接收到的串口数据的队列

        void Serial_Recv();
        void rx_parse();
        void processFrame(const frameHeader_t& fh_t, const std::vector<uint8_t>& frameBuffer);
        
        bool ack_notify_enqueue(ack_notify_struct_t t);
        bool reply_data_notify_enqueue(reply_data_notify_t t);
        bool data_request_notify_struct_enqueue(data_request_notify_struct_t t);

        bool ack_request_notify_struct_enqueue(ack_request_notify_struct_t t);
        bool noack_request_notify_struct_enqueue(noack_request_notify_struct_t t);


        
        
        int findFrameById(std::vector<frame_mgt_t>& cmd_queue, uint8_t target_frame_id);
        int findFrameByFuncCode(std::vector<frame_mgt_t>& cmd_queue, uint8_t target_func_code);
        int findRTXRemap(uint8_t func_code);

        uint16_t crc16(const uint8_t *data, size_t length) ;

        // DrLogger *logger_t;
};

#endif
