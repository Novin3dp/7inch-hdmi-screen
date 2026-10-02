/*
 * Goodix GT915 capacitive touch controller (I2C, 16-bit register addresses, big endian).
 *   0x8047..0x80FF  configuration (0x8048/49 = X resolution, 0x804A/4B = Y resolution, LE)
 *   0x8140          product id ("915")
 *   0x814E          status: bit7 = buffer ready, bits3..0 = number of touch points
 *   0x814F + 8*n    point n: id, x(LE16), y(LE16), size(LE16), reserved
 * Address 0x5D (0xBA/0xBB) is selected with the INT/RESET power-up sequence from the datasheet.
 */
#include "gt915.h"
#include "board.h"
#include "i2c.h"

#define TP_I2C  I2C2
#define TP_ADDR 0x5D

static struct gt915_info info;

static bool rd(uint16_t reg, uint8_t *buf, uint32_t n)
{
  uint8_t r[2] = {reg >> 8, reg & 0xFF};
  return i2c_xfer(TP_I2C, TP_ADDR, r, 2, 0, 0, buf, n);
}

static bool wr8(uint16_t reg, uint8_t v)
{
  uint8_t b[3] = {reg >> 8, reg & 0xFF, v};
  return i2c_xfer(TP_I2C, TP_ADDR, b, 3, 0, 0, 0, 0);
}

const struct gt915_info *gt915_info(void)
{
  return &info;
}

bool gt915_init(void)
{
  info.present = false;
  /* address 0xBA/0xBB: RESET low, INT low, RESET high after >100 us, INT low for >5 ms */
  gpio_write(PIN_TP_RST, 0);
  gpio_mode(PIN_TP_RST, MODE_OUT, PULL_NONE, 0, false);
  gpio_write(PIN_TP_INT, 0);
  gpio_mode(PIN_TP_INT, MODE_OUT, PULL_NONE, 0, false);
  delay_ms(11);
  gpio_write(PIN_TP_RST, 1);
  delay_ms(6);
  gpio_mode(PIN_TP_INT, MODE_IN, PULL_NONE, 0, false);   /* INT becomes the controller's output */
  delay_ms(60);

  uint8_t id[4] = {0};
  if (!rd(0x8140, id, 4)) {
    return false;
  }
  for (int i = 0; i < 4; i++) {
    info.product_id[i] = (char)id[i];
  }
  info.product_id[4] = 0;
  uint8_t cfg[5];
  if (rd(0x8047, cfg, 5)) {
    info.config_version = cfg[0];
    info.x_max = cfg[1] | (cfg[2] << 8);
    info.y_max = cfg[3] | (cfg[4] << 8);
  }
  if (info.x_max == 0 || info.y_max == 0) {
    info.x_max = 800;
    info.y_max = 480;
  }
  info.present = true;
  return true;
}

/* returns number of points (0..5), or -1 if nothing new / error */
int gt915_read(struct gt915_point *pts)
{
  if (!info.present) {
    return -1;
  }
  uint8_t s;
  if (!rd(0x814E, &s, 1)) {
    info.i2c_errors++;
    return -1;
  }
  if (!(s & 0x80)) {
    return -1;
  }
  int n = s & 0x0F;
  if (n > GT915_MAX_POINTS) {
    n = GT915_MAX_POINTS;
  }
  if (n) {
    uint8_t buf[8 * GT915_MAX_POINTS];
    if (!rd(0x814F, buf, 8 * n)) {
      info.i2c_errors++;
      wr8(0x814E, 0);
      return -1;
    }
    for (int i = 0; i < n; i++) {
      const uint8_t *p = buf + 8 * i;
      pts[i].id = p[0];
      pts[i].x = p[1] | (p[2] << 8);
      pts[i].y = p[3] | (p[4] << 8);
      pts[i].size = p[5] | (p[6] << 8);
    }
  }
  wr8(0x814E, 0);   /* release the buffer */
  return n;
}
