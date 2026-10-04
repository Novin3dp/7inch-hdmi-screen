/*
 * Clock (HSI48 + CRS locked to USB SOF, crystal-less), SysTick, GPIO defaults.
 */
#include "board.h"

uint32_t SystemCoreClock = 8000000;
static volatile uint32_t ms_ticks;

/* called from the startup code before main(): keep the reset clock, setup is done in board_init() */
void SystemInit(void) {}

void SysTick_Handler(void)
{
  ms_ticks++;
}

uint32_t millis(void)
{
  return ms_ticks;
}

void delay_ms(uint32_t ms)
{
  uint32_t t0 = ms_ticks;
  while ((uint32_t)(ms_ticks - t0) < ms + 1) {
    __WFI();
  }
}

void delay_us(uint32_t us)
{
  /* ~48 cycles per us; loop body is ~4 cycles */
  volatile uint32_t n = us * 12u;
  while (n--) {
  }
}

void gpio_mode(GPIO_TypeDef *port, int pin, int mode, int pull, int af, bool open_drain)
{
  port->MODER = (port->MODER & ~(3u << (2 * pin))) | ((uint32_t)mode << (2 * pin));
  port->PUPDR = (port->PUPDR & ~(3u << (2 * pin))) | ((uint32_t)pull << (2 * pin));
  port->OTYPER = (port->OTYPER & ~(1u << pin)) | ((open_drain ? 1u : 0u) << pin);
  port->OSPEEDR |= (3u << (2 * pin));
  volatile uint32_t *afr = &port->AFR[pin >> 3];
  *afr = (*afr & ~(0xFu << (4 * (pin & 7)))) | ((uint32_t)af << (4 * (pin & 7)));
}

static void clock_init(void)
{
  /* 48 MHz from the internal HSI48, trimmed by the CRS against USB start-of-frame packets */
  RCC->CR2 |= RCC_CR2_HSI48ON;
  while (!(RCC->CR2 & RCC_CR2_HSI48RDY)) {
  }
  FLASH->ACR = FLASH_ACR_PRFTBE | FLASH_ACR_LATENCY;    /* 1 wait state */
  RCC->CFGR = (RCC->CFGR & ~(RCC_CFGR_SW | RCC_CFGR_HPRE | RCC_CFGR_PPRE)) | RCC_CFGR_SW_HSI48;
  while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_HSI48) {
  }
  SystemCoreClock = 48000000;

  RCC->APB1ENR |= RCC_APB1ENR_CRSEN;
  CRS->CFGR = (CRS->CFGR & ~CRS_CFGR_SYNCSRC) | CRS_CFGR_SYNCSRC_1;   /* sync = USB SOF */
  CRS->CR |= CRS_CR_AUTOTRIMEN | CRS_CR_CEN;

  RCC->CFGR3 &= ~RCC_CFGR3_USBSW;                      /* USB clock = HSI48 */
  RCC->CFGR3 |= RCC_CFGR3_I2C1SW;                      /* I2C1 clock = SYSCLK (48 MHz) */

#ifdef BOARD_F042
  RCC->AHBENR |= RCC_AHBENR_GPIOAEN | RCC_AHBENR_GPIOBEN | RCC_AHBENR_GPIOFEN;
  RCC->APB2ENR |= RCC_APB2ENR_SYSCFGEN;
  RCC->APB1ENR |= RCC_APB1ENR_I2C1EN | RCC_APB1ENR_USART2EN | RCC_APB1ENR_TIM3EN | RCC_APB1ENR_USBEN;
  SYSCFG->CFGR1 |= SYSCFG_CFGR1_PA11_PA12_RMP;          /* TSSOP-20 pins 17/18 = PA11/PA12 (USB) */
#else
  RCC->AHBENR |= RCC_AHBENR_GPIOAEN | RCC_AHBENR_GPIOBEN;
  RCC->APB2ENR |= RCC_APB2ENR_SYSCFGEN | RCC_APB2ENR_USART1EN;
  RCC->APB1ENR |= RCC_APB1ENR_I2C1EN | RCC_APB1ENR_I2C2EN | RCC_APB1ENR_TIM3EN | RCC_APB1ENR_USBEN;
#endif
}

void board_init(void)
{
  clock_init();
  SysTick_Config(48000000 / 1000);

  /* safe defaults: everything that powers or resets something starts "off" */
  gpio_write(PIN_BIAS_EN, 0);
  gpio_mode(PIN_BIAS_EN, MODE_OUT, PULL_NONE, 0, false);
  gpio_write(PIN_LCD_RST, 0);
  gpio_mode(PIN_LCD_RST, MODE_OUT, PULL_NONE, 0, false);
  gpio_write(PIN_LT_RSTN, 0);
  gpio_mode(PIN_LT_RSTN, MODE_OUT, PULL_NONE, 0, false);
#if HAS_SCAN_PINS
  gpio_write(PIN_LCD_LR, 1);
  gpio_mode(PIN_LCD_LR, MODE_OUT, PULL_NONE, 0, false);
  gpio_write(PIN_LCD_UD, 0);
  gpio_mode(PIN_LCD_UD, MODE_OUT, PULL_NONE, 0, false);
#endif
  gpio_write(PIN_LED, 0);
  gpio_mode(PIN_LED, MODE_OUT, PULL_NONE, 0, false);
#if HAS_HDMI5V_DET
  gpio_mode(PIN_HDMI5V_DET, MODE_IN, PULL_NONE, 0, false);
#endif
  /* I2C pins: alternate function 1, open drain (external pull-ups) */
#ifdef BOARD_F042
  gpio_mode(PIN_I2C_SDA, MODE_AF, PULL_NONE, 1, true);
  gpio_mode(PIN_I2C_SCL, MODE_AF, PULL_NONE, 1, true);
#else
  gpio_mode(PIN_LT_SDA, MODE_AF, PULL_NONE, 1, true);
  gpio_mode(PIN_LT_SCL, MODE_AF, PULL_NONE, 1, true);
  gpio_mode(PIN_TP_SDA, MODE_AF, PULL_NONE, 1, true);
  gpio_mode(PIN_TP_SCL, MODE_AF, PULL_NONE, 1, true);
#endif
  gpio_write(PIN_BL_PWM, 0);
  gpio_mode(PIN_BL_PWM, MODE_OUT, PULL_NONE, 0, false);
  /* PA11/PA12 stay in their reset state: the USB peripheral takes them over when enabled */
}
