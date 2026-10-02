/*
 * User settings kept in the last 2 KB flash page (0x0801F800 on the 128 KB STM32F072CB).
 */
#include <string.h>
#include "settings.h"
#include "stm32f0xx.h"

#define SETTINGS_ADDR 0x0801F800u
#define SETTINGS_MAGIC 0x4C434431u   /* "LCD1" */

struct settings settings;

static uint32_t checksum(const struct settings *s)
{
  const uint8_t *p = (const uint8_t *)s;
  uint32_t c = 0x12345678;
  for (unsigned i = 0; i < offsetof(struct settings, sum); i++) {
    c = (c << 5) + c + p[i];
  }
  return c;
}

void settings_defaults(void)
{
  memset(&settings, 0, sizeof(settings));
  settings.magic = SETTINGS_MAGIC;
  settings.brightness = 80;
  settings.pclk_phase = 0x29;
  settings.rotate180 = 0;
  settings.touch_swap_xy = 0;
  settings.touch_invert_x = 0;
  settings.touch_invert_y = 0;
}

void settings_load(void)
{
  const struct settings *f = (const struct settings *)SETTINGS_ADDR;
  if (f->magic == SETTINGS_MAGIC && f->sum == checksum(f)) {
    memcpy(&settings, f, sizeof(settings));
  } else {
    settings_defaults();
  }
}

bool settings_save(void)
{
  settings.magic = SETTINGS_MAGIC;
  settings.sum = checksum(&settings);
  __disable_irq();
  FLASH->KEYR = FLASH_KEY1;
  FLASH->KEYR = FLASH_KEY2;
  while (FLASH->SR & FLASH_SR_BSY) {
  }
  FLASH->CR |= FLASH_CR_PER;
  FLASH->AR = SETTINGS_ADDR;
  FLASH->CR |= FLASH_CR_STRT;
  while (FLASH->SR & FLASH_SR_BSY) {
  }
  FLASH->SR = FLASH_SR_EOP;
  FLASH->CR &= ~FLASH_CR_PER;
  FLASH->CR |= FLASH_CR_PG;
  const uint16_t *src = (const uint16_t *)&settings;
  volatile uint16_t *dst = (volatile uint16_t *)SETTINGS_ADDR;
  for (unsigned i = 0; i < (sizeof(settings) + 1) / 2; i++) {
    dst[i] = src[i];
    while (FLASH->SR & FLASH_SR_BSY) {
    }
  }
  FLASH->SR = FLASH_SR_EOP;
  FLASH->CR &= ~FLASH_CR_PG;
  FLASH->CR |= FLASH_CR_LOCK;
  __enable_irq();
  return memcmp((const void *)SETTINGS_ADDR, &settings, sizeof(settings)) == 0;
}
