#ifndef USB_TOUCH_H
#define USB_TOUCH_H

#include <stdint.h>

#define REPORT_ID_TOUCH     1
#define REPORT_ID_MAX_COUNT 2
#define TOUCH_MAX_CONTACTS  5

/* one contact in the input report (6 bytes, little endian) */
struct __attribute__((packed)) touch_contact {
  uint8_t flags;   /* bit0 tip switch, bit1 in range */
  uint8_t id;
  uint16_t x;
  uint16_t y;
};

struct __attribute__((packed)) touch_report {
  struct touch_contact c[TOUCH_MAX_CONTACTS];
  uint8_t count;
};

#endif
