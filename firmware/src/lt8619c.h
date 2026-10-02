#ifndef LT8619C_H
#define LT8619C_H

#include <stdbool.h>
#include <stdint.h>

#define LT_CS_RGB      0x00
#define LT_CS_YCBCR422 0x20
#define LT_CS_YCBCR444 0x40
#define LT_QR_LIMITED  0x04
#define LT_QR_FULL     0x08

struct lt8619c_status {
  bool present, hpd, clk_stable, pll_locked, hsync_stable, hdmi_mode, video_ok;
  uint8_t chip_id[3];
  uint8_t vic, colorspace, colorimetry, quant_range, pr_factor;
  uint16_t h_active, v_active, h_sync, v_sync, h_bp, v_bp, h_total, v_total;
  uint16_t last_h_total, last_v_total;
  uint8_t h_pol, v_pol;
  uint32_t tmds_khz;
  uint32_t i2c_errors;
};

bool lt8619c_init(void);
bool lt8619c_poll(void);
void lt8619c_set_hpd(bool on);
void lt8619c_set_pclk_phase(uint8_t code);
uint8_t lt8619c_get_pclk_phase(void);
const struct lt8619c_status *lt8619c_status(void);

#endif
