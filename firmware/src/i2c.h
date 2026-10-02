#ifndef I2C_H
#define I2C_H

#include <stdbool.h>
#include <stdint.h>
#include "stm32f0xx.h"

/* TIMINGR values for a 48 MHz kernel clock (RM0091 table 83) */
#define I2C_TIMING_100K_48M 0xB0420F13u
#define I2C_TIMING_400K_48M 0x50330309u

void i2c_init(I2C_TypeDef *i2c, uint32_t timingr);
bool i2c_xfer(I2C_TypeDef *i2c, uint8_t addr7, const uint8_t *hdr, uint32_t hlen,
              const uint8_t *data, uint32_t dlen, uint8_t *rbuf, uint32_t rlen);
bool i2c_probe(I2C_TypeDef *i2c, uint8_t addr7);

#endif
