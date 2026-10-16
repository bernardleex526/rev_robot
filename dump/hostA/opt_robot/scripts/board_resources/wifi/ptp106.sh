#!/bin/bash

set -e

PTP4L_FILE="/lib/systemd/system/ptp4l.service"
PHC_FILE="/lib/systemd/system/phc2sys.service"

cat <<EOF > $PTP4L_FILE
[Unit]
Description=PTP (IEEE 1588) clock synchronization (ptp4l)
After=network.target
Requires=network-online.target

[Service]
Type=simple
ExecStart=/usr/sbin/ptp4l -H -E -4 -m -i eth0
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target

EOF

systemctl daemon-reload

systemctl enable ptp4l.service
systemctl restart ptp4l.service


PTP4L_FILE="/lib/systemd/system/ptp4leth1.service"

cat <<EOF > $PTP4L_FILE
[Unit]
Description=PTP (IEEE 1588) clock synchronization (ptp4l)
After=network.target
Requires=network-online.target

[Service]
Type=simple
ExecStart=/usr/sbin/ptp4l -H -E -4 -m -i eth1 
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target

EOF

systemctl daemon-reload

systemctl enable ptp4leth1.service
systemctl restart ptp4leth1.service



cat <<EOF > $PHC_FILE

[Unit]
Description=Synchronize PTP hardware clock (PHC) to system clock
After=ptp4l.service
Requires=ptp4l.service

[Service]
Type=simple
ExecStart=/usr/sbin/phc2sys -s CLOCK_REALTIME -c eth0  -m -w -O 0 
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target

EOF

systemctl daemon-reload

systemctl enable phc2sys.service
systemctl restart phc2sys.service

PHC_FILE="/lib/systemd/system/phc2syseth1.service"
cat <<EOF > $PHC_FILE

[Unit]
Description=Synchronize PTP hardware clock (PHC) to system clock
After=ptp4leth1.service
Requires=ptp4leth1.service

[Service]
Type=simple
ExecStart=/usr/sbin/phc2sys -s CLOCK_REALTIME  -c eth1  -m -w -O 0 
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target

EOF

systemctl daemon-reload

systemctl enable phc2syseth1.service
systemctl restart phc2syseth1.service


exit 0
