# Firmware for the AT070TN92 HDMI + USB touch board
#   ./fetch_deps.sh && make              -> build/lcd_touch.bin / .hex          (STM32F072CBT6 board, hardware/)
#   make BOARD=f042                      -> build_f042/lcd_touch_f042.bin / .hex (STM32F042F6P6 board, hardware_f042/)
#   make [BOARD=f042] flash-dfu          (hold BOOT while plugging USB, needs dfu-util)
BOARD   ?= f072
ifeq ($(BOARD),f042)
PROJECT  = lcd_touch_f042
BUILD    = build_f042
MCUDEF   = -DSTM32F042x6 -DBOARD_F042
LDSCRIPT = stm32f042f6.ld
STARTUP  = startup_stm32f042x6.s
else
PROJECT  = lcd_touch
BUILD    = build
MCUDEF   = -DSTM32F072xB
LDSCRIPT = stm32f072cb.ld
STARTUP  = startup_stm32f072xb.s
endif
CROSS   ?= arm-none-eabi-
CC       = $(CROSS)gcc
OBJCOPY  = $(CROSS)objcopy
SIZE     = $(CROSS)size
LIB      = lib
TUSB     = $(LIB)/tinyusb/src

SRC  = $(wildcard src/*.c)
SRC += $(TUSB)/tusb.c $(TUSB)/common/tusb_fifo.c $(TUSB)/device/usbd.c $(TUSB)/device/usbd_control.c \
       $(TUSB)/class/hid/hid_device.c $(TUSB)/portable/st/stm32_fsdev/dcd_stm32_fsdev.c
ASM  = $(LIB)/cmsis_device_f0/Source/Templates/gcc/$(STARTUP)

CFLAGS  = -mcpu=cortex-m0 -mthumb -Os -g3 -std=gnu11 -Wall -Wextra -Wno-unused-parameter \
          -ffunction-sections -fdata-sections $(MCUDEF) \
          -Isrc -I$(TUSB) -I$(LIB)/cmsis_device_f0/Include -I$(LIB)/cmsis_core
LDFLAGS = -mcpu=cortex-m0 -mthumb -T$(LDSCRIPT) -Wl,--gc-sections -Wl,-Map=$(BUILD)/$(PROJECT).map \
          --specs=nano.specs --specs=nosys.specs

OBJ = $(addprefix $(BUILD)/,$(notdir $(SRC:.c=.o))) $(BUILD)/startup.o
vpath %.c src $(TUSB) $(TUSB)/common $(TUSB)/device $(TUSB)/class/hid $(TUSB)/portable/st/stm32_fsdev

all: $(BUILD)/$(PROJECT).bin $(BUILD)/$(PROJECT).hex

$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD)/startup.o: $(ASM) | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD)/$(PROJECT).elf: $(OBJ)
	$(CC) $(LDFLAGS) $(OBJ) -o $@
	$(SIZE) $@
$(BUILD)/%.bin: $(BUILD)/%.elf
	$(OBJCOPY) -O binary $< $@
$(BUILD)/%.hex: $(BUILD)/%.elf
	$(OBJCOPY) -O ihex $< $@
$(BUILD):
	mkdir -p $(BUILD)

src/edid.h: tools/make_edid.py
	python3 tools/make_edid.py src/edid.h

flash-dfu: $(BUILD)/$(PROJECT).bin
	dfu-util -a 0 -s 0x08000000:leave -D $<

flash-stlink: $(BUILD)/$(PROJECT).bin
	st-flash --reset write $< 0x08000000

clean:
	rm -rf $(BUILD)
.PHONY: all clean flash-dfu flash-stlink
