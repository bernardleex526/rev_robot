#!/bin/bash
sudo cp 80-net-rename.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo cp dr_wifi.service /lib/systemd/system/
sudo systemctl enable dr_wifi.service
