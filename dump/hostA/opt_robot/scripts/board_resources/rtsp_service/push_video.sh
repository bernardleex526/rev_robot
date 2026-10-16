#!/bin/bash
#sudo bash /home/ysc/rtsp_service/usb_ctl.sh enable
sleep 3
sudo gst-launch-1.0 v4l2src device=/dev/video0 ! image/jpeg, width=800, height=600, framerate=30/1 ! jpegdec ! videoconvert ! mpph265enc gop=2 header-mode=each-idr !  h265parse config-interval=-1 !  rtspclientsink location=rtsp://127.0.0.1:8554/video1 latency=10 &
sudo gst-launch-1.0 v4l2src device=/dev/video2 ! image/jpeg, width=800, height=600, framerate=30/1 ! jpegdec ! videoconvert ! mpph265enc gop=2 header-mode=each-idr !  h265parse config-interval=-1 !  rtspclientsink location=rtsp://127.0.0.1:8554/video2 latency=10 &

