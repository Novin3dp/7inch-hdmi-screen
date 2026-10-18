/*
 * CH32X035C8T6: 48 MHz HSI (SystemInit), SysTick 1 ms, GPIO, TIM3 PWM, USART1, flash, USBFS.
 */
#include <string.h>
#include "board.h"
#include "tusb.h"

static volatile uint32_t ms_ticks;

__attribute__((interrupt)) void SysTick_Handler(void)
{
  SysTick->SR = 0;
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
  }
}

void delay_us(uint32_t us)
{
  /* SysTick counts HCLK (48 MHz) up to CMP: measure elapsed counts, handling the 1 ms wrap */
  uint32_t need = us * 48u, last = (uint32_t)SysTick->CNT, done = 0;
  const uint32_t period = (uint32_t)SysTick->CMP + 1u;
  while (done < need) {
    uint32_t now = (uint32_t)SysTick->CNT;
    done += (now >= last) ? now - last : now + period - last;
    last = now;
  }
}

void gpio_mode(GPIO_TypeDef *port, int pin, int mode, int pull, int af, bool open_drain)
{
  (void)af;
  (void)open_drain;
  GPIO_InitTypeDef g = {.GPIO_Pin = 1u << pin, .GPIO_Speed = GPIO_Speed_50MHz};
  switch (mode) {
  case MODE_OUT:
    g.GPIO_Mode = GPIO_Mode_Out_PP;
    break;
  case MODE_AF:
    g.GPIO_Mode = GPIO_Mode_AF_PP;
    break;
  case MODE_AN:
    g.GPIO_Mode = GPIO_Mode_AIN;
    break;
  default:
    g.GPIO_Mode = pull == PULL_UP ? GPIO_Mode_IPU : pull == PULL_DOWN ? GPIO_Mode_IPD : GPIO_Mode_IN_FLOATING;
    break;
  }
  GPIO_Init(port, &g);
}

void board_init(void)
{
  SystemCoreClockUpdate();
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO | RCC_APB2Periph_GPIOA | RCC_APB2Periph_GPIOB |
                         RCC_APB2Periph_GPIOC | RCC_APB2Periph_USART1, ENABLE);
  RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);
  RCC_AHBPeriphClockCmd(RCC_AHBPeriph_USBFS, ENABLE);

  SysTick->CTLR = 0;
  SysTick->SR = 0;
  SysTick->CNT = 0;
  SysTick->CMP = SystemCoreClock / 1000 - 1;
  SysTick->CTLR = 0xF;                      /* enable, interrupt, HCLK, auto reload */
  NVIC_EnableIRQ(SysTicK_IRQn);
  __enable_irq();

  /* safe defaults: everything that powers or resets something starts "off" */
  gpio_write(PIN_BIAS_EN, 0);
  gpio_mode(PIN_BIAS_EN, MODE_OUT, PULL_NONE, 0, false);
  gpio_write(PIN_LCD_RST, 0);
  gpio_mode(PIN_LCD_RST, MODE_OUT, PULL_NONE, 0, false);
  gpio_write(PIN_LT_RSTN, 0);
  gpio_mode(PIN_LT_RSTN, MODE_OUT, PULL_NONE, 0, false);
  gpio_write(PIN_LCD_LR, 1);
  gpio_mode(PIN_LCD_LR, MODE_OUT, PULL_NONE, 0, false);
  gpio_write(PIN_LCD_UD, 0);
  gpio_mode(PIN_LCD_UD, MODE_OUT, PULL_NONE, 0, false);
  gpio_write(PIN_LED, 0);
  gpio_mode(PIN_LED, MODE_OUT, PULL_NONE, 0, false);
  gpio_mode(PIN_HDMI5V_DET, MODE_IN, PULL_NONE, 0, false);
  gpio_write(PIN_BL_PWM, 0);
  gpio_mode(PIN_BL_PWM, MODE_OUT, PULL_NONE, 0, false);
}

/* ---- backlight PWM: TIM3_CH1 on PA6 (default mapping) ------------------------------- */
void bl_pwm_init(void)
{
  TIM3->CTLR1 = 0;
  TIM3->PSC = 0;
  TIM3->ATRLR = BL_PWM_TOP;
  TIM3->CHCTLR1 = (6u << 4) | (1u << 3);     /* OC1M = PWM mode 1, OC1PE */
  TIM3->CCER = 1u;                           /* CC1E */
  TIM3->CH1CVR = 0;
  TIM3->SWEVGR = 1u;                         /* UG */
  TIM3->CTLR1 = (1u << 7) | 1u;              /* ARPE, CEN */
}

void bl_pwm_out(uint32_t compare)
{
  TIM3->CH1CVR = compare;
  gpio_mode(PIN_BL_PWM, MODE_AF, PULL_NONE, 0, false);
}

/* ---- console: USART1 on PB10/PB11 ---------------------------------------------------- */
void uart_init(void)
{
  gpio_mode(PIN_UART_TX, MODE_AF, PULL_NONE, 0, false);
  gpio_mode(PIN_UART_RX, MODE_IN, PULL_UP, 0, false);
  USART_InitTypeDef u = {
    .USART_BaudRate = 115200,
    .USART_WordLength = USART_WordLength_8b,
    .USART_StopBits = USART_StopBits_1,
    .USART_Parity = USART_Parity_No,
    .USART_Mode = USART_Mode_Tx | USART_Mode_Rx,
    .USART_HardwareFlowControl = USART_HardwareFlowControl_None,
  };
  USART_Init(USART1, &u);
  USART_Cmd(USART1, ENABLE);
}

bool uart_tx_ready(void)
{
  return USART1->STATR & USART_FLAG_TXE;
}

void uart_tx(uint8_t c)
{
  USART1->DATAR = c;
}

int uart_rx(void)
{
  uint16_t st = USART1->STATR;
  if (st & USART_FLAG_ORE) {
    (void)USART1->DATAR;                     /* SR read + DR read clears overrun */
  }
  return (st & USART_FLAG_RXNE) ? (int)(USART1->DATAR & 0xFF) : -1;
}

/* ---- settings flash page (256-byte pages) ---------------------------------------------- */
bool flash_write_page(uint32_t addr, const void *data, uint32_t len)
{
  static uint32_t buf[64];                   /* one 256-byte page */
  memset(buf, 0xFF, sizeof(buf));
  memcpy(buf, data, len > sizeof(buf) ? sizeof(buf) : len);
  __disable_irq();
  bool ok = FLASH_ROM_ERASE(addr, 256) == FLASH_COMPLETE &&
            FLASH_ROM_WRITE(addr, buf, 256) == FLASH_COMPLETE;
  __enable_irq();
  return ok && memcmp((const void *)addr, data, len) == 0;
}

/* ---- USB full speed (USBFS), crystal-less, internal D+ pull-up, 3.3 V PHY --------------- */
__attribute__((interrupt)) void USBFS_IRQHandler(void)
{
  tud_int_handler(0);
}

__attribute__((interrupt)) void USBFSWakeUp_IRQHandler(void)
{
  tud_int_handler(0);
}

void board_usb_init(void)
{
  GPIO_InitTypeDef g = {.GPIO_Pin = GPIO_Pin_16, .GPIO_Speed = GPIO_Speed_50MHz, .GPIO_Mode = GPIO_Mode_IN_FLOATING};
  GPIO_Init(GPIOC, &g);
  g.GPIO_Pin = GPIO_Pin_17;
  g.GPIO_Mode = GPIO_Mode_IPU;
  GPIO_Init(GPIOC, &g);
  AFIO->CTLR = (AFIO->CTLR & ~(AFIO_CTLR_UDP_PUE | AFIO_CTLR_UDM_PUE)) | AFIO_CTLR_USB_PHY_V33 |
               AFIO_CTLR_UDP_PUE | AFIO_CTLR_USB_IOEN;
  NVIC_EnableIRQ(USBFS_IRQn);
}

/* TinyUSB asks for the time in OPT_OS_NONE mode */
uint32_t tusb_time_millis_api(void)
{
  return ms_ticks;
}
