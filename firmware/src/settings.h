#ifndef SETTINGS_H
#define SETTINGS_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

struct settings {
  uint32_t magic;
  uint8_t brightness;      /* 0..100 % */
  uint8_t pclk_phase;      /* LT8619C 0x60A2 */
  uint8_t rotate180;       /* panel L/R + U/D flipped, touch mirrored */
  uint8_t touch_swap_xy;
  uint8_t touch_invert_x;
  uint8_t touch_invert_y;
  uint8_t reserved[2];
  uint32_t sum;
};

extern struct settings settings;

void settings_defaults(void);
void settings_load(void);
bool settings_save(void);

#endif
