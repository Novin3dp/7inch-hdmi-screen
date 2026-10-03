# Out-of-tree build of the mainline Chipone ICN6211 DSI->RGB bridge driver
# (drivers/gpu/drm/bridge/chipone-icn6211.c), which Raspberry Pi OS kernels do not enable.
#   ./install.sh   fetches the source matching the running kernel, builds and installs it.
obj-m := chipone-icn6211.o
KDIR ?= /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(CURDIR) modules

install:
	$(MAKE) -C $(KDIR) M=$(CURDIR) modules_install
	depmod -a

clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) clean
