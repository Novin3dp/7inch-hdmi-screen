/*
 * AT070TN92 power sequencing and backlight.
 *
 * Datasheet 3.2 power-on order:  DVDD -> RESET -> VGL -> AVDD -> VGH -> data -> backlight
 *   - DVDD (3.3 V) is always on.
 *   - BIAS_EN switches the TPS61040 boost input: AVDD, VGL (inverting pump) and VGH (doubler,
 *     slower RC) ramp together, VGH last.
 *   - The backlight is only enabled ~200 ms after valid video is present (t10 = 180..200 ms).
 * Power-off is the reverse.
 */
#include "panel.h"
#include "board.h"

static uint8_t bl_percent = 80;
static bool bl_on, bias_on;

/* 48 MHz / (BL_PWM_TOP + 1) = 20 kHz PWM for the TPS61165 CTRL pin (timer set up in board.c) */
static void pwm_init(void)
{
  bl_pwm_init();
}

static void bl_apply(void)
{
  if (!bl_on || bl_percent == 0) {
    gpio_write(PIN_BL_PWM, 0);
    gpio_mode(PIN_BL_PWM, MODE_OUT, PULL_NONE, 0, false);
    return;
  }
  if (bl_percent >= 100) {
    gpio_write(PIN_BL_PWM, 1);
    gpio_mode(PIN_BL_PWM, MODE_OUT, PULL_NONE, 0, false);
    return;
  }
  bl_pwm_out((uint32_t)(BL_PWM_TOP + 1) * bl_percent / 100u);
}

void panel_set_orientation(bool rotate180)
{
#if HAS_SCAN_PINS
  /* datasheet note 4: U/D=GND, L/R=DVDD -> up->down, left->right (normal) */
  gpio_write(PIN_LCD_LR, !rotate180);
  gpio_write(PIN_LCD_UD, rotate180);
#else
  (void)rotate180;   /* scan direction strapped by R19/R20; "rot" then only turns the touch */
#endif
}

void panel_power_on(void)
{
  if (bias_on) {
    return;
  }
  pwm_init();
  gpio_write(PIN_LCD_RST, 0);
  delay_ms(5);                     /* DVDD already stable */
  gpio_write(PIN_LCD_RST, 1);      /* t1/t2: RESET released before the gate voltages */
  delay_ms(2);
  gpio_write(PIN_BIAS_EN, 1);      /* VGL, AVDD, then VGH (RC delayed) */
  delay_ms(40);
  bias_on = true;
}

void panel_power_off(void)
{
  panel_backlight(false);
  delay_ms(200);                   /* t11 */
  gpio_write(PIN_BIAS_EN, 0);
  delay_ms(30);
  gpio_write(PIN_LCD_RST, 0);
  bias_on = false;
}

void panel_backlight(bool on)
{
  if (on && !bl_on) {
    /* TPS61165: CTRL held high first selects PWM mode (not EasyScale) */
    gpio_write(PIN_BL_PWM, 1);
    gpio_mode(PIN_BL_PWM, MODE_OUT, PULL_NONE, 0, false);
    delay_ms(2);
  }
  bl_on = on;
  bl_apply();
}

void panel_set_brightness(uint8_t percent)
{
  bl_percent = percent > 100 ? 100 : percent;
  bl_apply();
}

uint8_t panel_get_brightness(void)
{
  return bl_percent;
}

bool panel_is_on(void)
{
  return bias_on;
}

bool panel_backlight_is_on(void)
{
  return bl_on;
}
