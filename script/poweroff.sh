#!/bin/bash
echo "heartbeat" > /sys/class/leds/imx6\:red\:front/trigger
systemctl stop kodi
echo 'tx 40 44 6C' | cec-client -s
#echo 'tx 45 44 6C' | cec-client -s   #This is optinal for AMP!
rm /storage/.kodi/userdata/status
echo "none" > /sys/class/leds/imx6\:red\:front/trigger
echo "0" > /sys/devices/soc0/pwmleds.24/leds/imx6\:red\:front/brightness
irexec -d /storage/.config/.lircrc &