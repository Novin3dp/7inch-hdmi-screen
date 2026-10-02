#ifndef PANEL_H
#define PANEL_H

#include <stdbool.h>
#include <stdint.h>

void panel_power_on(void);
void panel_power_off(void);
void panel_backlight(bool on);
void panel_set_brightness(uint8_t percent);
uint8_t panel_get_brightness(void);
void panel_set_orientation(bool rotate180);
bool panel_is_on(void);
bool panel_backlight_is_on(void);

#endif
