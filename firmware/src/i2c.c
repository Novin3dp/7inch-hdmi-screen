/*
 * Polling I2C master for the STM32F0 I2C v2 peripheral (I2C1 = LT8619C, I2C2 = GT915).
 * Supports transfers longer than 255 bytes (RELOAD) for the 256-byte EDID upload.
 */
#include "i2c.h"
#include "board.h"

#define I2C_TIMEOUT_MS 20

void i2c_init(I2C_TypeDef *i2c, uint32_t timingr)
{
  i2c->CR1 = 0;
  i2c->TIMINGR = timingr;
  i2c->CR1 = I2C_CR1_PE;
}

static void i2c_recover(I2C_TypeDef *i2c)
{
  uint32_t t = i2c->TIMINGR;
  i2c->CR1 = 0;          /* PE=0 resets the state machine and flags */
  delay_us(10);
  i2c->TIMINGR = t;
  i2c->CR1 = I2C_CR1_PE;
}

static bool wait_flag(I2C_TypeDef *i2c, uint32_t flag)
{
  uint32_t t0 = millis();
  while (!(i2c->ISR & flag)) {
    if (i2c->ISR & (I2C_ISR_NACKF | I2C_ISR_BERR | I2C_ISR_ARLO)) {
      return false;
    }
    if ((uint32_t)(millis() - t0) > I2C_TIMEOUT_MS) {
      return false;
    }
  }
  return true;
}

static uint32_t cr2_chunk(uint32_t left, bool last_phase)
{
  uint32_t n = left > 255 ? 255 : left;
  uint32_t v = n << I2C_CR2_NBYTES_Pos;
  if (left > 255) {
    v |= I2C_CR2_RELOAD;
  } else if (last_phase) {
    v |= I2C_CR2_AUTOEND;
  }
  return v;
}

/* write (hdr[hlen] + data[dlen]) and then optionally read rlen bytes with a repeated start */
bool i2c_xfer(I2C_TypeDef *i2c, uint8_t addr7, const uint8_t *hdr, uint32_t hlen,
              const uint8_t *data, uint32_t dlen, uint8_t *rbuf, uint32_t rlen)
{
  uint32_t total = hlen + dlen;
  bool ok = true;
  i2c->ICR = 0x3F38;  /* clear all flags */

  if (total) {
    uint32_t left = total, sent = 0, chunk_left;
    i2c->CR2 = ((uint32_t)addr7 << 1) | cr2_chunk(left, rlen == 0) | I2C_CR2_START;
    chunk_left = left > 255 ? 255 : left;
    while (left && ok) {
      if (!wait_flag(i2c, I2C_ISR_TXIS)) {
        ok = false;
        break;
      }
      i2c->TXDR = sent < hlen ? hdr[sent] : data[sent - hlen];
      sent++;
      left--;
      chunk_left--;
      if (chunk_left == 0 && left) {
        if (!wait_flag(i2c, I2C_ISR_TCR)) {
          ok = false;
          break;
        }
        i2c->CR2 = (i2c->CR2 & ~(I2C_CR2_NBYTES | I2C_CR2_RELOAD | I2C_CR2_AUTOEND)) |
                   cr2_chunk(left, rlen == 0);
        chunk_left = left > 255 ? 255 : left;
      }
    }
    if (ok && rlen) {
      ok = wait_flag(i2c, I2C_ISR_TC);
    }
  }
  if (ok && rlen) {
    uint32_t left = rlen, got = 0, chunk_left = rlen > 255 ? 255 : rlen;
    i2c->CR2 = ((uint32_t)addr7 << 1) | I2C_CR2_RD_WRN | cr2_chunk(left, true) | I2C_CR2_START;
    while (left && ok) {
      if (!wait_flag(i2c, I2C_ISR_RXNE)) {
        ok = false;
        break;
      }
      rbuf[got++] = (uint8_t)i2c->RXDR;
      left--;
      chunk_left--;
      if (chunk_left == 0 && left) {
        if (!wait_flag(i2c, I2C_ISR_TCR)) {
          ok = false;
          break;
        }
        i2c->CR2 = (i2c->CR2 & ~(I2C_CR2_NBYTES | I2C_CR2_RELOAD | I2C_CR2_AUTOEND)) | cr2_chunk(left, true);
        chunk_left = left > 255 ? 255 : left;
      }
    }
  }
  if (ok) {
    ok = wait_flag(i2c, I2C_ISR_STOPF);
  }
  if (!ok) {
    i2c->CR2 |= I2C_CR2_STOP;
    i2c_recover(i2c);
  }
  i2c->ICR = 0x3F38;
  return ok;
}

bool i2c_probe(I2C_TypeDef *i2c, uint8_t addr7)
{
  uint8_t dummy;
  return i2c_xfer(i2c, addr7, 0, 0, 0, 0, &dummy, 1);
}
