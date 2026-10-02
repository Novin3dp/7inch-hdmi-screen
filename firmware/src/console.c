/*
 * Debug / setup console on USART1 (PA9 TX, PA10 RX, 115200 8N1) - header J5 pins 5/6.
 * Type "help" for the command list.
 */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "console.h"
#include "board.h"
#include "gt915.h"
#include "lt8619c.h"
#include "panel.h"
#include "settings.h"

static char line[48];
static unsigned line_len;

void console_init(void)
{
  gpio_mode(PIN_UART_TX, MODE_AF, PULL_NONE, 1, false);
  gpio_mode(PIN_UART_RX, MODE_AF, PULL_UP, 1, false);
  USART1->CR1 = 0;
  USART1->BRR = 48000000 / 115200;
  USART1->CR1 = USART_CR1_TE | USART_CR1_RE | USART_CR1_UE;
}

static void putch(char c)
{
  uint32_t t0 = millis();
  while (!(USART1->ISR & USART_ISR_TXE)) {
    if ((uint32_t)(millis() - t0) > 5) {
      return;
    }
  }
  USART1->TDR = (uint8_t)c;
}

void console_printf(const char *fmt, ...)
{
  char buf[128];
  va_list ap;
  va_start(ap, fmt);
  int n = vsnprintf(buf, sizeof(buf), fmt, ap);
  va_end(ap);
  for (int i = 0; i < n && i < (int)sizeof(buf); i++) {
    if (buf[i] == '\n') {
      putch('\r');
    }
    putch(buf[i]);
  }
}

static void status(void)
{
  const struct lt8619c_status *s = lt8619c_status();
  const struct gt915_info *t = gt915_info();
  console_printf("LT8619C: %s id %02x %02x %02x  hpd=%d clk=%d pll=%d hsync=%d video=%d %s\n",
                 s->present ? "ok" : "NOT FOUND", s->chip_id[0], s->chip_id[1], s->chip_id[2], s->hpd,
                 s->clk_stable, s->pll_locked, s->hsync_stable, s->video_ok, s->hdmi_mode ? "HDMI" : "DVI");
  console_printf("  input %ux%u total %ux%u hs %u hbp %u vs %u vbp %u tmds %lu kHz cs 0x%02x i2c_err %lu\n",
                 s->h_active, s->v_active, s->h_total, s->v_total, s->h_sync, s->h_bp, s->v_sync, s->v_bp,
                 (unsigned long)s->tmds_khz, s->colorspace, (unsigned long)s->i2c_errors);
  console_printf("GT915: %s product '%s' cfg v%u res %ux%u i2c_err %lu\n", t->present ? "ok" : "NOT FOUND",
                 t->product_id, t->config_version, t->x_max, t->y_max, (unsigned long)t->i2c_errors);
  console_printf("panel: bias=%d backlight=%d brightness=%u%% phase=0x%02x rot180=%u swap=%u invx=%u invy=%u\n",
                 panel_is_on(), panel_backlight_is_on(), panel_get_brightness(), lt8619c_get_pclk_phase(),
                 settings.rotate180, settings.touch_swap_xy, settings.touch_invert_x, settings.touch_invert_y);
  console_printf("HDMI +5V: %s\n", gpio_read(PIN_HDMI5V_DET) ? "present" : "absent");
}

static const uint8_t phase_codes[] = {0x20, 0x28, 0x21, 0x29, 0x22, 0x2a, 0x23, 0x2b, 0x24, 0x2c};

static void command(char *c)
{
  char *arg = strchr(c, ' ');
  int v = arg ? atoi(arg + 1) : -1;
  if (arg) {
    *arg = 0;
  }
  if (!strcmp(c, "status") || !strcmp(c, "s")) {
    status();
  } else if (!strcmp(c, "bl") && v >= 0) {
    settings.brightness = (uint8_t)(v > 100 ? 100 : v);
    panel_set_brightness(settings.brightness);
  } else if (!strcmp(c, "phase") && v >= 0 && v < 10) {
    settings.pclk_phase = phase_codes[v];
    lt8619c_set_pclk_phase(settings.pclk_phase);
  } else if (!strcmp(c, "rot") && v >= 0) {
    settings.rotate180 = v ? 1 : 0;
    panel_set_orientation(settings.rotate180);
  } else if (!strcmp(c, "swap")) {
    settings.touch_swap_xy ^= 1;
  } else if (!strcmp(c, "invx")) {
    settings.touch_invert_x ^= 1;
  } else if (!strcmp(c, "invy")) {
    settings.touch_invert_y ^= 1;
  } else if (!strcmp(c, "save")) {
    console_printf(settings_save() ? "saved\n" : "save FAILED\n");
  } else if (!strcmp(c, "defaults")) {
    settings_defaults();
  } else if (!strcmp(c, "dfu")) {
    console_printf("use the BOOT button: hold BOOT, plug USB -> STM32 DFU bootloader\n");
  } else {
    console_printf("commands: status | bl <0..100> | phase <0..9> | rot <0|1> | swap | invx | invy | "
                   "save | defaults\n");
  }
}

void console_poll(void)
{
  while (USART1->ISR & USART_ISR_RXNE) {
    char ch = (char)USART1->RDR;
    if (ch == '\r' || ch == '\n') {
      if (line_len) {
        line[line_len] = 0;
        console_printf("\n");
        command(line);
        line_len = 0;
      }
    } else if (line_len < sizeof(line) - 1) {
      line[line_len++] = ch;
      putch(ch);
    }
  }
  if (USART1->ISR & USART_ISR_ORE) {
    USART1->ICR = USART_ICR_ORECF;
  }
}
