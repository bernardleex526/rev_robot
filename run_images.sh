#!/bin/bash
# Image all M20 Pro compute hosts sequentially (read-only, resumable).
cd /home/lee/rea
./image_host.sh 10.21.41.1   hostA_103
./image_host.sh 10.21.31.104 hostB_104
./image_host.sh 10.21.31.106 hostC_106
echo "ALL_IMAGES_DONE"
