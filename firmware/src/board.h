/*
 * AT070TN92 HDMI + USB touch driver board - pin map and low level helpers.
 *   default:      STM32F072CBT6 board, pins must match hardware/gen/design.py (U10)
 *   BOARD_F042:   STM32F042F6P6 board, pins must match hardware_f042/gen/design.py (U10)
 */
#ifndef BOARD_H
#define BOARD_H

#include <stdbool.h>
#include <stdint.h>
#include "stm32f0xx.h"

/* ---- GPIO map ------------------------------------------------------------------ */
#ifdef BOARD_F042
/* TSSOP-20: one I2C bus shared by LT8619C (0x32) and GT915 (0x5D); panel scan direction is set by
 * resistors (R19/R20), there is no HDMI +5V sense input; USB on PA11/PA12 remapped to pins 17/18. */
#define PIN_LT_RSTN      GPIOA, 0    /* LT8619C RESET_N (10k pull-down)                     */
#define PIN_BIAS_EN      GPIOA, 1    /* high = AVDD/VGH/VGL bias supply on                   */
#define PIN_UART_TX      GPIOA, 2    /* USART2 (AF1) debug console, 115200 8N1               */
#define PIN_UART_RX      GPIOA, 3
#define PIN_LCD_RST      GPIOA, 4    /* panel RESET (active low, 10k pull-down)             */
#define PIN_LED          GPIOA, 5
#define PIN_BL_PWM       GPIOA, 6    /* TIM3_CH1 (AF1) -> TPS61165 CTRL                     */
#define PIN_TP_RST       GPIOA, 7
#define PIN_TP_INT       GPIOB, 1
#define PIN_I2C_SDA      GPIOF, 0    /* I2C1 (AF1), shared bus                              */
#define PIN_I2C_SCL      GPIOF, 1
#define LT_I2C           I2C1
#define TP_I2C           I2C1
#define CONSOLE_USART    USART2
#define HAS_SCAN_PINS    0
#define HAS_HDMI5V_DET   0
#else
#define PIN_HDMI5V_DET   GPIOA, 0    /* HDMI +5V divided 22k/33k (3.0 V when cable present) */
#define PIN_BL_PWM       GPIOA, 6    /* TIM3_CH1 (AF1) -> TPS61165 CTRL                     */
#define PIN_BIAS_EN      GPIOA, 8    /* high = AVDD/VGH/VGL bias supply on                   */
#define PIN_UART_TX      GPIOA, 9    /* USART1 (AF1) debug console, 115200 8N1               */
#define PIN_UART_RX      GPIOA, 10
#define PIN_LCD_RST      GPIOB, 0    /* panel RESET (active low, 10k pull-down)             */
#define PIN_LCD_LR       GPIOB, 1    /* panel L/R scan direction                            */
#define PIN_LCD_UD       GPIOB, 2    /* panel U/D scan direction                            */
#define PIN_LT_RSTN      GPIOB, 5    /* LT8619C RESET_N (10k pull-down)                     */
#define PIN_LT_SCL       GPIOB, 6    /* I2C1 (AF1) -> LT8619C (private bus)                 */
#define PIN_LT_SDA       GPIOB, 7
#define PIN_TP_SCL       GPIOB, 10   /* I2C2 (AF1) -> GT915 touch controller                */
#define PIN_TP_SDA       GPIOB, 11
#define PIN_TP_INT       GPIOB, 12
#define PIN_TP_RST       GPIOB, 13
#define PIN_LED          GPIOB, 15
#define LT_I2C           I2C1
#define TP_I2C           I2C2
#define CONSOLE_USART    USART1
#define HAS_SCAN_PINS    1
#define HAS_HDMI5V_DET   1
#endif

/* ---- helpers --------------------------------------------------------------------- */
enum { MODE_IN = 0, MODE_OUT = 1, MODE_AF = 2, MODE_AN = 3 };
enum { PULL_NONE = 0, PULL_UP = 1, PULL_DOWN = 2 };

void gpio_mode(GPIO_TypeDef *port, int pin, int mode, int pull, int af, bool open_drain);
static inline void gpio_write(GPIO_TypeDef *port, int pin, bool v)
{
  port->BSRR = v ? (1u << pin) : (1u << (pin + 16));
}
static inline bool gpio_read(GPIO_TypeDef *port, int pin)
{
  return (port->IDR >> pin) & 1u;
}

void board_init(void);
uint32_t millis(void);
void delay_ms(uint32_t ms);
void delay_us(uint32_t us);

#endif
