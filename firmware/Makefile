# Firmware for the AT070TN92 HDMI + USB touch board (STM32F072CBT6)
#   ./fetch_deps.sh && make            -> build/lcd_touch.bin / .hex
#   make flash-dfu                       (hold BOOT while plugging USB, needs dfu-util)
PROJECT  = lcd_touch
CROSS   ?= arm-none-eabi-
CC       = $(CROSS)gcc
OBJCOPY  = $(CROSS)objcopy
SIZE     = $(CROSS)size
LIB      = lib
TUSB     = $(LIB)/tinyusb/src

SRC  = $(wildcard src/*.c)
SRC += $(TUSB)/tusb.c $(TUSB)/common/tusb_fifo.c $(TUSB)/device/usbd.c $(TUSB)/device/usbd_control.c \
       $(TUSB)/class/hid/hid_device.c $(TUSB)/portable/st/stm32_fsdev/dcd_stm32_fsdev.c
ASM  = $(LIB)/cmsis_device_f0/Source/Templates/gcc/startup_stm32f072xb.s

CFLAGS  = -mcpu=cortex-m0 -mthumb -Os -g3 -std=gnu11 -Wall -Wextra -Wno-unused-parameter \
          -ffunction-sections -fdata-sections -DSTM32F072xB \
          -Isrc -I$(TUSB) -I$(LIB)/cmsis_device_f0/Include -I$(LIB)/cmsis_core
LDFLAGS = -mcpu=cortex-m0 -mthumb -Tstm32f072cb.ld -Wl,--gc-sections -Wl,-Map=build/$(PROJECT).map \
          --specs=nano.specs --specs=nosys.specs

OBJ = $(addprefix build/,$(notdir $(SRC:.c=.o))) build/startup.o
vpath %.c src $(TUSB) $(TUSB)/common $(TUSB)/device $(TUSB)/class/hid $(TUSB)/portable/st/stm32_fsdev

all: build/$(PROJECT).bin build/$(PROJECT).hex

build/%.o: %.c | build
	$(CC) $(CFLAGS) -c $< -o $@
build/startup.o: $(ASM) | build
	$(CC) $(CFLAGS) -c $< -o $@
build/$(PROJECT).elf: $(OBJ)
	$(CC) $(LDFLAGS) $(OBJ) -o $@
	$(SIZE) $@
build/%.bin: build/%.elf
	$(OBJCOPY) -O binary $< $@
build/%.hex: build/%.elf
	$(OBJCOPY) -O ihex $< $@
build:
	mkdir -p build

src/edid.h: tools/make_edid.py
	python3 tools/make_edid.py src/edid.h

flash-dfu: build/$(PROJECT).bin
	dfu-util -a 0 -s 0x08000000:leave -D $<

flash-stlink: build/$(PROJECT).bin
	st-flash --reset write $< 0x08000000

clean:
	rm -rf build
.PHONY: all clean flash-dfu flash-stlink
