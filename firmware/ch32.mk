# CH32X035C8T6 build (dual-MCU board, hardware_dual/), included by the Makefile for BOARD=ch32.
#   needs a RISC-V toolchain: riscv-none-elf-gcc (xPack) or riscv64-unknown-elf-gcc + picolibc
#   ./fetch_deps.sh ch32 && make BOARD=ch32   -> build_ch32/lcd_touch_ch32.bin / .hex
PROJECT  = lcd_touch_ch32
BUILD    = build_ch32
CROSS   ?= $(shell command -v riscv-none-elf-gcc >/dev/null && echo riscv-none-elf- || echo riscv64-unknown-elf-)
CC       = $(CROSS)gcc
OBJCOPY  = $(CROSS)objcopy
SIZE     = $(CROSS)size
SDK      = lib/ch32x035_ug/EVT/EXAM/SRC
TUSB     = lib/tinyusb_master/src
BSP      = lib/tinyusb_master/hw/bsp/ch32x035

SRC  = $(filter-out src/syscalls.c,$(wildcard src/*.c)) $(wildcard src/ch32/*.c)
SRC += $(TUSB)/tusb.c $(TUSB)/common/tusb_fifo.c $(TUSB)/device/usbd.c \
       $(TUSB)/class/hid/hid_device.c $(TUSB)/portable/wch/dcd_ch32_usbfs.c
SRC += $(SDK)/Core/core_riscv.c $(BSP)/system_ch32x035.c \
       $(SDK)/Peripheral/src/ch32x035_gpio.c $(SDK)/Peripheral/src/ch32x035_rcc.c \
       $(SDK)/Peripheral/src/ch32x035_usart.c $(SDK)/Peripheral/src/ch32x035_flash.c \
       $(SDK)/Peripheral/src/ch32x035_misc.c
ASM  = $(SDK)/Startup/startup_ch32x035.S

ARCH    = -march=rv32imac_zicsr_zifencei -mabi=ilp32 -mcmodel=medany -msmall-data-limit=8
CFLAGS  = $(ARCH) -Os -g3 -std=gnu11 -Wall -Wextra -Wno-unused-parameter -ffunction-sections -fdata-sections \
          -DMCU_CH32X035 -DSYSCLK_FREQ_48MHz_HSI=48000000 \
          -Isrc/ch32 -Isrc -I$(TUSB) -I$(BSP) -I$(SDK)/Core -I$(SDK)/Peripheral/inc
LDFLAGS = $(ARCH) -nostartfiles -Tch32x035c8.ld -Wl,--gc-sections -Wl,-Map=$(BUILD)/$(PROJECT).map
ifeq ($(CROSS),riscv64-unknown-elf-)
CFLAGS  += --specs=picolibc.specs
LDFLAGS += --specs=picolibc.specs
else
LDFLAGS += --specs=nano.specs --specs=nosys.specs
endif

OBJ = $(addprefix $(BUILD)/,$(notdir $(SRC:.c=.o))) $(BUILD)/startup.o
vpath %.c src src/ch32 $(TUSB) $(TUSB)/common $(TUSB)/device $(TUSB)/class/hid $(TUSB)/portable/wch \
          $(SDK)/Core $(SDK)/Peripheral/src $(BSP)

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

# USB bootloader (hold SW2 while plugging USB): https://github.com/ch32-rs/wchisp
flash-isp: $(BUILD)/$(PROJECT).bin
	wchisp flash $<
# WCH-LinkE on J5 (SWDIO/SWCLK): wlink from https://github.com/ch32-rs/wlink
flash-wlink: $(BUILD)/$(PROJECT).bin
	wlink flash $<

clean:
	rm -rf $(BUILD)
.PHONY: all clean flash-isp flash-wlink
