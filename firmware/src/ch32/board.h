/*
 * AT070TN92 HDMI + USB touch driver board - CH32X035C8T6 (RISC-V) on the dual-MCU board
 * (hardware_dual/: same LQFP-48 footprint as the STM32F072CBT6). Pins = board nets of U10.
 *
 * NEVER drive PA15, PA22, PA23, PB3, PB4, PB12, PB13: they sit on the STM32 supply pins
 * (1, 8, 9, 23, 24, 35, 36) and are hard-wired to 3.3 V / GND. They stay floating inputs.
 */
#ifndef BOARD_H
#define BOARD_H

#include <stdbool.h>
#include <stdint.h>
#include "ch32x035.h"

/* ---- GPIO map (LQFP-48 pin in brackets) ------------------------------------------------ */
#define PIN_HDMI5V_DET   GPIOA, 0    /* [10] HDMI +5V divided 22k/33k                        */
#define PIN_BL_PWM       GPIOA, 6    /* [16] TIM3_CH1 -> TPS61169 CTRL                       */
#define PIN_LCD_RST      GPIOC, 6    /* [18] panel RESET (10k pull-down)                     */
#define PIN_LCD_LR       GPIOC, 7    /* [19] panel L/R scan direction                        */
#define PIN_LCD_UD       GPIOB, 0    /* [20] panel U/D scan direction                        */
#define PIN_TP_SCL       GPIOB, 1    /* [21] GT915 bus, bit-banged                           */
#define PIN_TP_SDA       GPIOB, 2    /* [22]                                                 */
#define PIN_TP_INT       GPIOB, 5    /* [25] */
#define PIN_TP_RST       GPIOB, 6    /* [26] */
#define PIN_LED          GPIOB, 8    /* [28] */
#define PIN_BIAS_EN      GPIOB, 9    /* [29] AVDD/VGH/VGL bias supply on                     */
#define PIN_UART_TX      GPIOB, 10   /* [30] USART1 TX (default mapping)                     */
#define PIN_UART_RX      GPIOB, 11   /* [31] USART1 RX                                       */
#define PIN_LT_RSTN      GPIOA, 9    /* [41] LT8619C RESET_N (10k pull-down)                 */
#define PIN_LT_SCL       GPIOA, 10   /* [42] LT8619C bus, bit-banged                         */
#define PIN_LT_SDA       GPIOA, 11   /* [43]                                                 */
#define HAS_SCAN_PINS    1
#define HAS_HDMI5V_DET   1
#define BOOT_HINT        "CH32: hold SW2 (D+ high) while plugging USB, WCHISPTool / wchisp"

/* I2C: the CH32X035 I2C block is unusable on some lots, so both buses are bit-banged */
typedef struct sw_i2c {
  GPIO_TypeDef *scl_port;
  int scl_pin;
  GPIO_TypeDef *sda_port;
  int sda_pin;
  uint32_t half_period_us;
} i2c_bus_t;
extern i2c_bus_t lt_bus, tp_bus;
#define LT_I2C (&lt_bus)
#define TP_I2C (&tp_bus)

/* ---- helpers --------------------------------------------------------------------------- */
enum { MODE_IN = 0, MODE_OUT = 1, MODE_AF = 2, MODE_AN = 3 };
enum { PULL_NONE = 0, PULL_UP = 1, PULL_DOWN = 2 };

/* af is ignored (CH32 uses the default/remapped mapping); open_drain is emulated by the I2C code */
void gpio_mode(GPIO_TypeDef *port, int pin, int mode, int pull, int af, bool open_drain);
static inline void gpio_write(GPIO_TypeDef *port, int pin, bool v)
{
  port->BSHR = v ? (1u << pin) : (1u << (pin + 16));
}
static inline bool gpio_read(GPIO_TypeDef *port, int pin)
{
  return (port->INDR >> pin) & 1u;
}

void board_init(void);
void board_i2c_init(void);
void board_usb_init(void);
uint32_t millis(void);
void delay_ms(uint32_t ms);
void delay_us(uint32_t us);

#define BL_PWM_TOP 2399
void bl_pwm_init(void);
void bl_pwm_out(uint32_t compare);
void uart_init(void);
bool uart_tx_ready(void);
void uart_tx(uint8_t c);
int uart_rx(void);
bool flash_write_page(uint32_t addr, const void *data, uint32_t len);

#endif
