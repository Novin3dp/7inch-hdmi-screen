/*
 * Lontium LT8619C: HDMI 1.4 receiver -> 24-bit TTL RGB (SDR, DE mode) for the AT070TN92.
 *
 * Lontium does not publish a register map.  The register sequence below follows the open-source
 * drivers that Lontium's reference code was released in (Hardkernel u-boot
 * board/hardkernel/odroid-common/lt8619c.c and the Rockchip/Linux V4L2 lt8619c driver, both GPL-2.0)
 * which is why this file is GPL-2.0-or-later.
 *
 *   bank 0x60: RX PHY / PLL / CSC / TTL output timing      bank 0x80: HPD / EDID / clock detect / infoframes
 */
#include <string.h>
#include "lt8619c.h"
#include "board.h"
#include "edid.h"
#include "i2c.h"

#define LT_I2C  I2C1
#define LT_ADDR 0x32        /* 7-bit (0x64/0x65) */

static uint8_t cur_bank = 0xFF;
static bool i2c_err;

static void wr(uint8_t reg, uint8_t val)
{
  uint8_t b[2] = {reg, val};
  if (!i2c_xfer(LT_I2C, LT_ADDR, b, 2, 0, 0, 0, 0)) {
    i2c_err = true;
  }
  if (reg == 0xFF) {
    cur_bank = val;
  }
}

static uint8_t rd(uint8_t reg)
{
  uint8_t v = 0;
  if (!i2c_xfer(LT_I2C, LT_ADDR, &reg, 1, 0, 0, &v, 1)) {
    i2c_err = true;
  }
  return v;
}

static void bank(uint8_t b)
{
  if (cur_bank != b) {
    wr(0xFF, b);
  }
}

static void set_bits(uint8_t reg, uint8_t mask, bool on)
{
  uint8_t v = rd(reg);
  wr(reg, on ? (v | mask) : (v & ~mask));
}

/* ------------------------------------------------------------------------------------------- */
static struct lt8619c_status st;
static uint8_t pclk_phase = 0x29;   /* 0x60A2: 0x20,0x28,0x21,0x29,0x22,0x2a,0x23,0x2b,0x24,0x2c */

const struct lt8619c_status *lt8619c_status(void)
{
  return &st;
}

void lt8619c_set_hpd(bool on)
{
  bank(0x80);
  set_bits(0x06, 0x08, on);
  st.hpd = on;
}

static void load_edid(void)
{
  static uint8_t buf[256];
  memcpy(buf, edid_800x480, 128);
  memset(buf + 128, 0, 128);
  bank(0x80);
  wr(0x8E, 0x07);            /* EDID RAM write enable */
  wr(0x8F, 0x00);            /* start address */
  uint8_t reg = 0x90;
  if (!i2c_xfer(LT_I2C, LT_ADDR, &reg, 1, buf, sizeof(buf), 0, 0)) {
    i2c_err = true;
  }
  wr(0x8E, 0x02);            /* back to normal: EDID served on the DDC bus */
}

static void rx_init(void)
{
  bank(0x80);
  set_bits(0x2C, 0x30, true);      /* RGD_CLK_STABLE_OPT */
  bank(0x60);
  wr(0x04, 0xF2);
  wr(0x83, 0x3F);
  wr(0x80, 0x08);                  /* system clock = 25 MHz crystal */
  wr(0xA4, 0x10);                  /* SDR pixel clock output */
  wr(0x07, 0xFF);
  wr(0xA8, 0x0F);
  wr(0x60, 0x00);
  wr(0x96, 0x71);
  wr(0xA0, 0x50);
  wr(0xA3, 0x74);                  /* PCLK phase adjust enable, PCLK on the PCLK pin */
  wr(0xA2, pclk_phase);
  wr(0x6D, 0x00);                  /* default mapping: D0-7 = R, D8-15 = G, D16-23 = B */
  wr(0x6E, 0x00);
  wr(0x0E, 0xFD);                  /* reset / release the TTL output FIFO */
  wr(0x0E, 0xFF);
  wr(0x0D, 0xFC);
  wr(0x0D, 0xFF);
}

static void rx_reset(void)
{
  bank(0x60);
  wr(0x0E, 0xBF);                  /* reset RX PLL */
  wr(0x09, 0xFD);                  /* reset RX PLL lock detect */
  delay_ms(5);
  wr(0x0E, 0xFF);
  wr(0x09, 0xFF);
  wr(0x0E, 0xC7);                  /* reset PI */
  wr(0x09, 0x0F);                  /* reset RX, CDR */
  delay_ms(10);
  wr(0x0E, 0xFF);
  delay_ms(10);
  wr(0x09, 0x8F);
  delay_ms(10);
  wr(0x09, 0xFF);
  delay_ms(50);
}

bool lt8619c_init(void)
{
  memset(&st, 0, sizeof(st));
  i2c_err = false;
  cur_bank = 0xFF;
  gpio_write(PIN_LT_RSTN, 0);
  delay_ms(10);
  gpio_write(PIN_LT_RSTN, 1);
  delay_ms(20);                    /* chip needs ~10 ms after reset before the first I2C access */

  bank(0x60);
  st.chip_id[0] = rd(0x00);
  st.chip_id[1] = rd(0x01);
  st.chip_id[2] = rd(0x02);
  st.present = !i2c_err && st.chip_id[0] == 0x16 && st.chip_id[1] == 0x04;
  if (!st.present) {
    return false;
  }
  lt8619c_set_hpd(false);
  load_edid();
  delay_ms(100);
  rx_init();
  /* audio is not used on this board: leave I2S/SPDIF disabled */
  lt8619c_set_hpd(true);
  return !i2c_err;
}

static bool detect_clock(void)
{
  bank(0x80);
  if (!(rd(0x44) & 0x08)) {                       /* TMDS clock not stable */
    st.clk_stable = st.pll_locked = st.hsync_stable = false;
    return false;
  }
  if (!st.clk_stable) {
    st.clk_stable = true;
    bank(0x60);
    wr(0x97, rd(0x97) & 0x3F);
    bank(0x80);
    wr(0x1B, 0x00);
    rx_reset();
    delay_ms(5);
  }
  bank(0x80);
  st.pll_locked = (rd(0x87) & 0x10) != 0;
  if (!st.pll_locked) {
    st.clk_stable = st.hsync_stable = false;
  }
  return st.pll_locked;
}

static void input_info(void)
{
  bank(0x80);
  if (!(rd(0x13) & 0x01)) {
    st.hsync_stable = false;
    return;
  }
  if (!st.hsync_stable) {
    for (int i = 0; i < 8; i++) {                 /* must stay stable for ~160 ms */
      delay_ms(20);
      bank(0x80);
      if (!(rd(0x13) & 0x01)) {
        return;
      }
    }
    st.hsync_stable = true;
    bank(0x60);
    uint8_t v = rd(0x0D);                          /* reset the BT/TTL FIFO */
    wr(0x0D, v & 0xF8);
    wr(0x0D, v | 0x06);
    wr(0x0D, v | 0x01);
  }
  bank(0x80);
  st.hdmi_mode = (rd(0x13) & 0x02) != 0;
  if (st.hdmi_mode) {
    st.vic = rd(0x74) & 0x7F;
    st.colorspace = rd(0x71) & 0x60;
    st.colorimetry = rd(0x72) & 0xC0;
    st.quant_range = rd(0x73) & 0x0C;
    st.pr_factor = rd(0x75) & 0x0F;
  } else {
    st.vic = 0;
    st.colorspace = LT_CS_RGB;
    st.colorimetry = 0x80;
    st.quant_range = LT_QR_FULL;
    st.pr_factor = 0;
  }
  uint8_t r97, r1b;
  if (st.pr_factor == 1) {
    r97 = 0x40, r1b = 0x20;
  } else if (st.pr_factor == 3) {
    r97 = 0x80, r1b = 0x60;
  } else {
    r97 = 0x00, r1b = 0x00;
  }
  bank(0x60);
  wr(0x97, (rd(0x97) & 0x3F) | r97);
  bank(0x80);
  wr(0x1B, r1b);
}

static void csc(void)
{
  /* output is always RGB; convert YCbCr inputs and expand limited-range RGB */
  uint8_t r52 = 0x00, r53 = 0x00;
  if (st.colorspace == LT_CS_RGB) {
    r53 = (st.quant_range == LT_QR_LIMITED) ? 0x08 : 0x00;
  } else {
    r52 = (st.colorspace == LT_CS_YCBCR422) ? 0x01 : 0x00;
    bool bt601 = st.colorimetry == 0x40;
    if (st.quant_range == LT_QR_FULL) {
      r53 = bt601 ? 0x40 : 0x60;
    } else {
      r53 = bt601 ? 0x50 : 0x70;
    }
  }
  bank(0x60);
  wr(0x07, 0xFE);
  wr(0x52, r52);
  wr(0x53, r53);
}

static void read_timing(void)
{
  bank(0x60);
  st.h_active = ((uint16_t)rd(0x22) << 8) | rd(0x23);
  st.v_active = ((uint16_t)(rd(0x20) & 0x0F) << 8) | rd(0x21);
  st.h_sync = ((uint16_t)(rd(0x14) & 0x0F) << 8) | rd(0x15);
  st.v_sync = rd(0x13);
  st.h_bp = ((uint16_t)(rd(0x18) & 0x0F) << 8) | rd(0x19);
  st.v_bp = rd(0x16);
  st.h_total = ((uint16_t)rd(0x1E) << 8) | rd(0x1F);
  st.v_total = ((uint16_t)(rd(0x1C) & 0x0F) << 8) | rd(0x1D);
  uint8_t pol = rd(0x24);
  st.h_pol = pol & 1;
  st.v_pol = (pol >> 1) & 1;
  bank(0x80);
  st.tmds_khz = ((uint32_t)(rd(0x44) & 0x07) << 16) | ((uint32_t)rd(0x45) << 8) | rd(0x46);
}

static void wait_tx_pll_lock(void)
{
  /* 0x60A3 bit6 (set by rx_init) enables the output PLL; kick it until it reports lock */
  bank(0x60);
  if (!(rd(0xA3) & 0x40)) {
    return;
  }
  for (int i = 0; i < 10; i++) {
    bank(0x80);
    if (rd(0x87) & 0x20) {
      return;
    }
    bank(0x60);
    wr(0x0E, rd(0x0E) & 0xFD);
    delay_ms(5);
    wr(0x0E, 0xFF);
  }
}

static void output_timing(void)
{
  /* TTL output timing = detected input timing (pass-through, no scaler) */
  wait_tx_pll_lock();
  bank(0x60);
  uint8_t v = rd(0x60) & 0xC7;
  if (st.h_pol) v |= 0x20;
  if (st.v_pol) v |= 0x10;
  wr(0x68, 0x00);
  wr(0x60, v);
  uint16_t t = st.h_sync + st.h_bp;
  wr(0x61, t >> 8);
  wr(0x62, t & 0xFF);
  wr(0x63, st.h_active >> 8);
  wr(0x64, st.h_active & 0xFF);
  wr(0x65, st.h_total >> 8);
  wr(0x66, st.h_total & 0xFF);
  wr(0x67, (uint8_t)(st.v_sync + st.v_bp));
  wr(0x69, st.v_active >> 8);
  wr(0x6A, st.v_active & 0xFF);
  wr(0x6B, st.v_total >> 8);
  wr(0x6C, st.v_total & 0xFF);
}

/* call every ~100 ms; returns true while a stable picture is being output */
bool lt8619c_poll(void)
{
  if (!st.present) {
    return false;
  }
  i2c_err = false;
  bool was_ok = st.video_ok;
  st.video_ok = false;
  if (detect_clock()) {
    input_info();
    if (st.hsync_stable) {
      read_timing();
      if (!was_ok || st.h_total != st.last_h_total || st.v_total != st.last_v_total) {
        csc();
        output_timing();
        st.last_h_total = st.h_total;
        st.last_v_total = st.v_total;
      }
      st.video_ok = st.h_active > 0 && st.v_active > 0;
    }
  }
  if (i2c_err) {
    st.i2c_errors++;
  }
  return st.video_ok;
}

void lt8619c_set_pclk_phase(uint8_t code)
{
  pclk_phase = code;
  if (st.present) {
    bank(0x60);
    wr(0xA2, code);
  }
}

uint8_t lt8619c_get_pclk_phase(void)
{
  return pclk_phase;
}
