# HDMI7 دو-میکرو: STM32F072CBT6 یا CH32X035C8T6 روی یک جای نصب

این پروژه همان برد HDMI7 اصلی (`hardware/`، 80×50mm، USB-C در لبه‌ی راست) است، با یک فوت‌پرینت LQFP-48 (U10) که **هر دو میکرو** روی آن می‌نشینند. اول STM32F072 را نصب و برد را تست کنید، بعد آن را با هوای گرم بردارید و CH32X035C8T6 را جایش لحیم کنید.

> ⚠️ همه‌ی بررسی‌های نرم‌افزاری پاس شده‌اند (DRC بدون خطا و بدون اتصال باز، تطبیق شماتیک با PCB، کامپایل فرم‌ور هر دو میکرو)، ولی برد و فرم‌ور CH32 **هنوز روی سخت‌افزار تست نشده‌اند**.

![top](../docs/img/dual_pcb_top.png)

## چرا یک فوت‌پرینت کافی است

پایه‌های اصلی دو تراشه در LQFP-48 یکی‌اند:

| پایه | STM32F072 | CH32X035C8T6 |
|---|---|---|
| 7 | NRST | PA21/RST |
| 32 / 33 | USB D− / D+ | USB D− / D+ |
| 34 / 37 | SWDIO / SWCLK | SWDIO / SWCLK |
| 47 / 48 | VSS / VDD | GND / VDD |

همه‌ی سیگنال‌های برد روی CH32 هم به یک GPIO قابل استفاده می‌رسند:

| پایه | سیگنال | STM32F072 | CH32X035 |
|---|---|---|---|
| 10 | HDMI5V_DET | PA0 | PA0 |
| 16 | BL_PWM | PA6 (TIM3_CH1) | PA6 (TIM3_CH1) |
| 18 / 19 / 20 | LCD_RST / LR / UD | PB0 / PB1 / PB2 | PC6 / PC7 / PB0 |
| 21 / 22 | TP_SCL / TP_SDA | PB10 / PB11 (I2C2) | PB1 / PB2 (I2C نرم‌افزاری) |
| 25 / 26 | TP_INT / TP_RST | PB12 / PB13 | PB5 / PB6 |
| 28 / 29 | LED / BIAS_EN | PB15 / PA8 | PB8 / PB9 |
| 30 / 31 | UART TX / RX | PA9 / PA10 (USART1) | PB10 / PB11 (USART1) |
| 41 | LT_RSTN | PB5 | PA9 |
| 42 / 43 | LT_SCL / LT_SDA | PB6 / PB7 (I2C1) | PA10 / PA11 (I2C نرم‌افزاری) |
| 44 | BOOT0 | BOOT0 | PA12 (استفاده نمی‌شود) |

I2C روی CH32 نرم‌افزاری است، چون I2C سخت‌افزاری آن در بعضی سری‌های تولید ایراد دارد.

**نکته‌ی مهم برای فرم‌ور CH32:** پایه‌های تغذیه‌ی STM32 (۱، ۸، ۹، ۲۳، ۲۴، ۳۵، ۳۶) روی CH32 پایه‌ی GPIO هستند (PA15، PA22، PA23، PB3، PB4، PB12، PB13) که به 3.3V یا زمین وصل شده‌اند. فرم‌ور CH32 **هرگز نباید این پایه‌ها را خروجی کند**؛ بعد از ریست ورودی هستند و همین‌طور باید بمانند.

## بوت‌لودر

* **STM32F072:** دکمه‌ی SW1 (BOOT0) را نگه دارید و USB را وصل کنید ← DFU.
* **CH32X035:** دکمه‌ی SW2 را نگه دارید و USB را وصل کنید. SW2 پایه‌ی D+ (PC17) را از طریق R38 (4.7k) به 3.3V می‌برد و تراشه وارد بوت‌لودر USB می‌شود (WCHISPTool یا `wchisp`). برنامه‌ریزی با WCH-LinkE روی هدر J5 (SWDIO/SWCLK) هم ممکن است. SW2 روی STM32 بی‌اثر است.

## فرم‌ور

هر دو میکرو از همان کد `firmware/` استفاده می‌کنند؛ فقط لایه‌ی سخت‌افزار (کلاک، GPIO، PWM، UART، فلش، I2C) جداست (`firmware/src/stm32/` و `firmware/src/ch32/`).

```sh
cd firmware
./fetch_deps.sh ch32          # SDK رسمی WCH (EVT) + TinyUSB master (درایور USB برای CH32X035)
make                          # STM32F072  -> build/lcd_touch.bin
make BOARD=ch32               # CH32X035C8T6 -> build_ch32/lcd_touch_ch32.bin  (28.9KB فلش، ~5KB رم)
make BOARD=ch32 flash-isp     # بوت‌لودر USB (SW2 را هنگام وصل کردن USB نگه دارید)، با wchisp
make BOARD=ch32 flash-wlink   # یا با WCH-LinkE روی J5
```

کامپایلر RISC-V لازم است: `riscv-none-elf-gcc` (xPack) یا در اوبونتو `gcc-riscv64-unknown-elf` + `picolibc-riscv64-unknown-elf`.

تفاوت‌های نسخه‌ی CH32:
* هر دو باس I2C نرم‌افزاری (bit-bang) هستند: LT8619C حدود 100kHz و GT915 حدود 250kHz، با پشتیبانی از clock stretching و آزادسازی باس گیرکرده در شروع.
* USB: کنترلر USBFS داخلی، بدون کریستال، مقاومت pull-up داخلی روی D+ و PHY در حالت 3.3V.
* تنظیمات در آخرین صفحه‌ی ۲۵۶ بایتی فلش (0x0800F700) ذخیره می‌شوند.
* دستورهای کنسول (`status`، `bl`، `phase`، `rot`، ...) و رفتار برد همان نسخه‌ی STM32 است.

## تعویض میکرو

1. با STM32F072 و فرم‌ور `firmware/` (`make`) برد را کامل تست کنید.
2. STM32 را با هوای گرم بردارید، پدها را با فتیله تمیز کنید.
3. CH32X035C8T6 را با **همان جهت پایه‌ی ۱** لحیم کنید.

## ساخت

`fab/lcd_dual_gerbers.zip`، `fab/bom_jlcpcb.csv` (با STM32F072)، `fab/cpl_jlcpcb.csv`؛ شماتیک: `docs/schematic_dual.pdf`. برای ساخت دوباره، اسکریپت‌های `hardware_dual/gen` مثل بخش ۱۰ README اصلی اجرا می‌شوند.
