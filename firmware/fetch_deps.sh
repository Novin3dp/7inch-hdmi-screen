#!/bin/sh
# Downloads the third-party sources needed to build the firmware into ./lib
set -e
cd "$(dirname "$0")"
mkdir -p lib
[ -d lib/tinyusb ] || git clone -q --depth 1 --branch 0.17.0 https://github.com/hathach/tinyusb.git lib/tinyusb
[ -d lib/cmsis_device_f0 ] || git clone -q --depth 1 https://github.com/STMicroelectronics/cmsis_device_f0.git lib/cmsis_device_f0
mkdir -p lib/cmsis_core
for f in core_cm0.h cmsis_compiler.h cmsis_gcc.h cmsis_version.h; do
  [ -f lib/cmsis_core/$f ] || curl -sSL -o lib/cmsis_core/$f \
    https://raw.githubusercontent.com/ARM-software/CMSIS_5/5.9.0/CMSIS/Core/Include/$f
done
echo "dependencies ready"
