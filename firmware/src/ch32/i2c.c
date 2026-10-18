/*
 * Bit-banged I2C master (open drain emulated: drive low / release to the external pull-ups).
 * The CH32X035 hardware I2C is not usable on some silicon lots, and on this board the buses
 * sit on pins without an I2C function anyway.  Supports clock stretching (timeout).
 */
#include "i2c.h"
#include "board.h"

i2c_bus_t lt_bus = {GPIOA, 10, GPIOA, 11, 5};   /* LT8619C, ~100 kHz */
i2c_bus_t tp_bus = {GPIOB, 1, GPIOB, 2, 2};     /* GT915, ~250 kHz  */

static inline void line(GPIO_TypeDef *port, int pin, bool high)
{
  if (high) {
    gpio_mode(port, pin, MODE_IN, PULL_NONE, 0, false);     /* released: pull-up takes it high */
  } else {
    gpio_write(port, pin, 0);
    gpio_mode(port, pin, MODE_OUT, PULL_NONE, 0, false);
  }
}

#define SCL(b, v) line((b)->scl_port, (b)->scl_pin, (v))
#define SDA(b, v) line((b)->sda_port, (b)->sda_pin, (v))
#define SDA_IN(b) gpio_read((b)->sda_port, (b)->sda_pin)
#define WAIT(b)   delay_us((b)->half_period_us)

static bool scl_high(i2c_bus_t *b)
{
  SCL(b, 1);
  uint32_t t0 = millis();
  while (!gpio_read(b->scl_port, b->scl_pin)) {        /* clock stretching */
    if ((uint32_t)(millis() - t0) > 5) {
      return false;
    }
  }
  return true;
}

static void start(i2c_bus_t *b)
{
  SDA(b, 1);
  scl_high(b);
  WAIT(b);
  SDA(b, 0);
  WAIT(b);
  SCL(b, 0);
}

static void stop(i2c_bus_t *b)
{
  SDA(b, 0);
  WAIT(b);
  scl_high(b);
  WAIT(b);
  SDA(b, 1);
  WAIT(b);
}

static bool write_byte(i2c_bus_t *b, uint8_t v)
{
  for (int i = 7; i >= 0; i--) {
    SDA(b, (v >> i) & 1);
    WAIT(b);
    if (!scl_high(b)) {
      return false;
    }
    WAIT(b);
    SCL(b, 0);
  }
  SDA(b, 1);                                             /* release for ACK */
  WAIT(b);
  if (!scl_high(b)) {
    return false;
  }
  bool ack = !SDA_IN(b);
  WAIT(b);
  SCL(b, 0);
  return ack;
}

static uint8_t read_byte(i2c_bus_t *b, bool ack)
{
  uint8_t v = 0;
  SDA(b, 1);
  for (int i = 0; i < 8; i++) {
    WAIT(b);
    scl_high(b);
    v = (uint8_t)((v << 1) | SDA_IN(b));
    WAIT(b);
    SCL(b, 0);
  }
  SDA(b, !ack);
  WAIT(b);
  scl_high(b);
  WAIT(b);
  SCL(b, 0);
  SDA(b, 1);
  return v;
}

static void bus_init(i2c_bus_t *b)
{
  SDA(b, 1);
  SCL(b, 1);
  /* free a slave that was stopped mid-byte: up to 9 clocks until SDA is high, then STOP */
  for (int i = 0; i < 9 && !SDA_IN(b); i++) {
    SCL(b, 0);
    WAIT(b);
    SCL(b, 1);
    WAIT(b);
  }
  stop(b);
}

void board_i2c_init(void)
{
  bus_init(&lt_bus);
  bus_init(&tp_bus);
}

bool i2c_xfer(i2c_bus_t *b, uint8_t addr7, const uint8_t *hdr, uint32_t hlen,
              const uint8_t *data, uint32_t dlen, uint8_t *rbuf, uint32_t rlen)
{
  bool ok = true;
  if (hlen + dlen) {
    start(b);
    ok = write_byte(b, (uint8_t)(addr7 << 1));
    for (uint32_t i = 0; ok && i < hlen; i++) {
      ok = write_byte(b, hdr[i]);
    }
    for (uint32_t i = 0; ok && i < dlen; i++) {
      ok = write_byte(b, data[i]);
    }
  }
  if (ok && rlen) {
    start(b);                                            /* (repeated) start */
    ok = write_byte(b, (uint8_t)((addr7 << 1) | 1));
    for (uint32_t i = 0; ok && i < rlen; i++) {
      rbuf[i] = read_byte(b, i + 1 < rlen);
    }
  }
  stop(b);
  return ok;
}

bool i2c_probe(i2c_bus_t *b, uint8_t addr7)
{
  uint8_t dummy;
  return i2c_xfer(b, addr7, 0, 0, 0, 0, &dummy, 1);
}
