/*
 * AT070TN92 HDMI + USB touch driver board firmware (STM32F072CBT6)
 *
 *  - powers the panel in the order required by the AT070TN92 datasheet
 *  - configures the LT8619C HDMI receiver (EDID 800x480@60, RGB888, DE mode)
 *  - backlight only while a valid picture is received
 *  - reads the GT915 touch controller and reports a 5-point USB HID touch screen
 *
 * SPDX-License-Identifier: GPL-2.0-or-later  (lt8619c.c follows GPL Lontium/Hardkernel code)
 */
#include "board.h"
#include "console.h"
#include "gt915.h"
#include "i2c.h"
#include "lt8619c.h"
#include "panel.h"
#include "settings.h"
#include "tusb.h"
#include "usb_touch.h"

void USB_IRQHandler(void)
{
  tud_int_handler(0);
}

static struct touch_report report;
static bool touch_dirty;

static void map_point(const struct gt915_point *p, struct touch_contact *c)
{
  const struct gt915_info *t = gt915_info();
  uint32_t px = p->x, py = p->y, xm = t->x_max, ym = t->y_max;
  if (settings.touch_swap_xy) {
    uint32_t tmp = px;
    px = py;
    py = tmp;
    tmp = xm;
    xm = ym;
    ym = tmp;
  }
  px = px * 800u / (xm ? xm : 800u);
  py = py * 480u / (ym ? ym : 480u);
  if (px > 799) px = 799;
  if (py > 479) py = 479;
  bool ix = settings.touch_invert_x ^ settings.rotate180;
  bool iy = settings.touch_invert_y ^ settings.rotate180;
  c->x = (uint16_t)(ix ? 799 - px : px);
  c->y = (uint16_t)(iy ? 479 - py : py);
}

static void touch_task(void)
{
  static uint32_t last;
  static uint8_t prev_ids[TOUCH_MAX_CONTACTS], prev_n;
  if ((uint32_t)(millis() - last) < 8) {
    return;
  }
  last = millis();
  struct gt915_point pts[GT915_MAX_POINTS];
  int n = gt915_read(pts);
  if (n < 0) {
    return;
  }
  /* report current contacts, plus a final "lifted" entry for contacts that disappeared */
  struct touch_report r = {0};
  int k = 0;
  for (int i = 0; i < n && k < TOUCH_MAX_CONTACTS; i++, k++) {
    r.c[k].flags = 0x03;
    r.c[k].id = pts[i].id & 0x7F;
    map_point(&pts[i], &r.c[k]);
  }
  for (int j = 0; j < prev_n && k < TOUCH_MAX_CONTACTS; j++) {
    bool still = false;
    for (int i = 0; i < n; i++) {
      still |= (pts[i].id & 0x7F) == prev_ids[j];
    }
    if (!still) {
      for (int q = 0; q < TOUCH_MAX_CONTACTS; q++) {
        if (report.c[q].id == prev_ids[j]) {
          r.c[k] = report.c[q];
        }
      }
      r.c[k].flags = 0x00;   /* tip switch released */
      r.c[k].id = prev_ids[j];
      k++;
    }
  }
  r.count = (uint8_t)k;
  prev_n = (uint8_t)n;
  for (int i = 0; i < n; i++) {
    prev_ids[i] = pts[i].id & 0x7F;
  }
  if (k || touch_dirty) {
    report = r;
    touch_dirty = true;
  }
}

static void usb_task(void)
{
  if (touch_dirty && tud_hid_ready()) {
    tud_hid_report(REPORT_ID_TOUCH, &report, sizeof(report));
    touch_dirty = false;
  }
}

static void video_task(void)
{
  static uint32_t last, video_since;
  static bool video;
  if ((uint32_t)(millis() - last) < 100) {
    return;
  }
  last = millis();
  bool ok = lt8619c_poll();
  if (ok && !video) {
    video_since = millis();
    console_printf("video: %ux%u\n", lt8619c_status()->h_active, lt8619c_status()->v_active);
  }
  if (!ok && video) {
    console_printf("video lost\n");
    panel_backlight(false);
  }
  video = ok;
  /* backlight 200 ms (datasheet t10) after the picture became stable */
  if (video && !panel_backlight_is_on() && (uint32_t)(millis() - video_since) > 200) {
    panel_set_brightness(settings.brightness);
    panel_backlight(true);
  }
  gpio_write(PIN_LED, video ? 1 : ((millis() / 500) & 1));
}

int main(void)
{
  board_init();
  console_init();
  settings_load();
  console_printf("\nAT070TN92 HDMI touch board\n");

#ifdef BOARD_F042
  i2c_init(I2C1, I2C_TIMING_400K_48M);   /* one bus: LT8619C and GT915 both support 400 kHz */
#else
  i2c_init(I2C1, I2C_TIMING_100K_48M);
  i2c_init(I2C2, I2C_TIMING_400K_48M);
#endif

  panel_set_orientation(settings.rotate180);
  panel_power_on();

  lt8619c_set_pclk_phase(settings.pclk_phase);
  if (!lt8619c_init()) {
    console_printf("LT8619C not responding\n");
  }
  if (!gt915_init()) {
    console_printf("GT915 not responding\n");
  }

  tusb_init();
  NVIC_EnableIRQ(USB_IRQn);

  for (;;) {
    tud_task();
    video_task();
    touch_task();
    usb_task();
    console_poll();
    if (!lt8619c_status()->present) {
      static uint32_t retry;
      if ((uint32_t)(millis() - retry) > 2000) {
        retry = millis();
        lt8619c_init();
      }
    }
  }
}
