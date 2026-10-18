#ifndef I2C_H
#define I2C_H

#include <stdbool.h>
#include <stdint.h>
#include "board.h"   /* i2c_bus_t, LT_I2C, TP_I2C */

/* both buses are set up by board_i2c_init(); STM32: I2C peripheral, CH32: bit-banged */
bool i2c_xfer(i2c_bus_t *bus, uint8_t addr7, const uint8_t *hdr, uint32_t hlen,
              const uint8_t *data, uint32_t dlen, uint8_t *rbuf, uint32_t rlen);
bool i2c_probe(i2c_bus_t *bus, uint8_t addr7);

#endif
