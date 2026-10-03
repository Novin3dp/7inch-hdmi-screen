#!/bin/sh
# Build and install the ICN6211 bridge driver + the AT070TN92 DSI overlay on a Raspberry Pi.
#   sudo apt install linux-headers-rpi-v8 device-tree-compiler   (Pi 5: linux-headers-rpi-2712)
#   sudo ./install.sh
set -e
cd "$(dirname "$0")"
KVER=$(uname -r)
BRANCH="rpi-$(echo "$KVER" | cut -d. -f1-2).y"
SRC="https://raw.githubusercontent.com/raspberrypi/linux/$BRANCH/drivers/gpu/drm/bridge/chipone-icn6211.c"
if [ ! -d "/lib/modules/$KVER/build" ]; then
    echo "kernel headers for $KVER missing: sudo apt install linux-headers-rpi-v8 (or -rpi-2712 on a Pi 5)"
    exit 1
fi
echo "fetching $SRC"
wget -q -O chipone-icn6211.c "$SRC"
make
make install
OVL=/boot/firmware/overlays
[ -d "$OVL" ] || OVL=/boot/overlays
dtc -@ -I dts -O dtb -o "$OVL/at070tn92-dsi.dtbo" ../at070tn92-dsi-overlay.dts
CFG=/boot/firmware/config.txt
[ -f "$CFG" ] || CFG=/boot/config.txt
grep -q "^dtoverlay=at070tn92-dsi" "$CFG" || printf '\n[all]\ndtoverlay=vc4-kms-v3d\ndtoverlay=at070tn92-dsi\n' >> "$CFG"
echo "done: reboot (Pi 5 DISP0 / CM DSI0 port: change the line to dtoverlay=at070tn92-dsi,dsi0)"
