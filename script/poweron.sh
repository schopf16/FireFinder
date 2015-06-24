#!/bin/bash
echo "heartbeat" > /sys/class/leds/imx6\:red\:front/trigger
killall irexec
#echo 'tx 45 44 6D' | cec-client -s    # This is optional for AMP
echo 'tx 40 44 6D' | cec-client -s
echo 1 >> /storage/.kodi/userdata/status
echo "none" > /sys/class/leds/imx6\:red\:front/trigger
echo "248" > /sys/class/leds/imx6\:red\:front/brightness
systemctl start kodi