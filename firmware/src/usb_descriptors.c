/*
 * USB device: one HID interface, multi-touch digitizer ("Touch Screen", 5 contacts).
 * Works with the Linux hid-multitouch driver (Raspberry Pi OS) without any configuration.
 */
#include <string.h>
#include "tusb.h"
#include "usb_touch.h"

/* pid.codes test VID/PID - replace with your own for a product */
#define USB_VID 0x1209
#define USB_PID 0x0001

static const tusb_desc_device_t desc_device = {
    .bLength = sizeof(tusb_desc_device_t),
    .bDescriptorType = TUSB_DESC_DEVICE,
    .bcdUSB = 0x0200,
    .bDeviceClass = 0x00,
    .bDeviceSubClass = 0x00,
    .bDeviceProtocol = 0x00,
    .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,
    .idVendor = USB_VID,
    .idProduct = USB_PID,
    .bcdDevice = 0x0100,
    .iManufacturer = 0x01,
    .iProduct = 0x02,
    .iSerialNumber = 0x03,
    .bNumConfigurations = 0x01,
};

uint8_t const *tud_descriptor_device_cb(void)
{
  return (uint8_t const *)&desc_device;
}

/* X/Y logical range = panel pixels; physical size = active area 154.08 x 85.92 mm */
#define FINGER(n)                                                                    \
  0x05, 0x0D,             /*   Usage Page (Digitizer)                       */      \
  0x09, 0x22,             /*   Usage (Finger)                               */      \
  0xA1, 0x02,             /*   Collection (Logical)                         */      \
  0x09, 0x42,             /*     Usage (Tip Switch)                         */      \
  0x15, 0x00, 0x25, 0x01, 0x75, 0x01, 0x95, 0x01, 0x81, 0x02,                     \
  0x09, 0x32,             /*     Usage (In Range)                           */      \
  0x81, 0x02,                                                                        \
  0x75, 0x06, 0x95, 0x01, 0x81, 0x03,  /* 6 bit padding                    */      \
  0x09, 0x51,             /*     Usage (Contact Identifier)                 */      \
  0x25, 0x7F, 0x75, 0x08, 0x95, 0x01, 0x81, 0x02,                                 \
  0x05, 0x01,             /*     Usage Page (Generic Desktop)               */      \
  0x55, 0x0E, 0x65, 0x11, /*     Unit exponent -2, unit cm                  */      \
  0x35, 0x00,                                                                        \
  0x26, 0x1F, 0x03,       /*     Logical max 799                            */      \
  0x46, 0x02, 0x06,       /*     Physical max 1538 (15.38 cm)               */      \
  0x75, 0x10, 0x95, 0x01,                                                            \
  0x09, 0x30, 0x81, 0x02, /*     X                                          */      \
  0x26, 0xDF, 0x01,       /*     Logical max 479                            */      \
  0x46, 0x5B, 0x03,       /*     Physical max 859                           */      \
  0x09, 0x31, 0x81, 0x02, /*     Y                                          */      \
  0x55, 0x00, 0x65, 0x00, 0x45, 0x00, /* reset unit / exponent / phys. max */      \
  0xC0                    /*   End Collection                               */

static const uint8_t desc_hid_report[] = {
    0x05, 0x0D,                      /* Usage Page (Digitizer)         */
    0x09, 0x04,                      /* Usage (Touch Screen)           */
    0xA1, 0x01,                      /* Collection (Application)       */
    0x85, REPORT_ID_TOUCH,           /*   Report ID                    */
    FINGER(0), FINGER(1), FINGER(2), FINGER(3), FINGER(4),
    0x05, 0x0D,                      /*   Usage Page (Digitizer)       */
    0x09, 0x54,                      /*   Usage (Contact Count)        */
    0x15, 0x00, 0x25, 0x7F, 0x75, 0x08, 0x95, 0x01, 0x81, 0x02,
    0x85, REPORT_ID_MAX_COUNT,       /*   Report ID (feature)          */
    0x09, 0x55,                      /*   Usage (Contact Count Maximum)*/
    0x25, TOUCH_MAX_CONTACTS, 0x75, 0x08, 0x95, 0x01, 0xB1, 0x02,
    0xC0                             /* End Collection                 */
};

uint8_t const *tud_hid_descriptor_report_cb(uint8_t instance)
{
  (void)instance;
  return desc_hid_report;
}

enum { ITF_NUM_HID, ITF_NUM_TOTAL };
#define EPNUM_HID 0x81
#define CONFIG_TOTAL_LEN (TUD_CONFIG_DESC_LEN + TUD_HID_DESC_LEN)

static const uint8_t desc_configuration[] = {
    TUD_CONFIG_DESCRIPTOR(1, ITF_NUM_TOTAL, 0, CONFIG_TOTAL_LEN, 0x00, 100),
    TUD_HID_DESCRIPTOR(ITF_NUM_HID, 0, HID_ITF_PROTOCOL_NONE, sizeof(desc_hid_report), EPNUM_HID,
                       CFG_TUD_HID_EP_BUFSIZE, 5),
};

uint8_t const *tud_descriptor_configuration_cb(uint8_t index)
{
  (void)index;
  return desc_configuration;
}

static const char *const string_desc[] = {
    "",                          /* 0: language (handled below) */
    "DIY",                       /* 1: manufacturer */
    "AT070TN92 HDMI Touch",      /* 2: product */
};

static uint16_t desc_str[33];

uint16_t const *tud_descriptor_string_cb(uint8_t index, uint16_t langid)
{
  (void)langid;
  uint8_t n;
  if (index == 0) {
    desc_str[1] = 0x0409;
    n = 1;
  } else if (index == 3) {
    /* serial = 96-bit unique device id */
    const uint32_t *uid = (const uint32_t *)0x1FFFF7ACu;   /* 96-bit unique ID (RM0091 33.1) */
    static const char hex[] = "0123456789ABCDEF";
    n = 0;
    for (int w = 0; w < 3; w++) {
      for (int i = 7; i >= 0; i--) {
        desc_str[1 + n++] = hex[(uid[w] >> (4 * i)) & 0xF];
      }
    }
  } else {
    if (index >= sizeof(string_desc) / sizeof(string_desc[0])) {
      return NULL;
    }
    const char *s = string_desc[index];
    n = (uint8_t)strlen(s);
    if (n > 32) {
      n = 32;
    }
    for (uint8_t i = 0; i < n; i++) {
      desc_str[1 + i] = s[i];
    }
  }
  desc_str[0] = (uint16_t)((TUSB_DESC_STRING << 8) | (2 * n + 2));
  return desc_str;
}

/* feature report: maximum number of contacts */
uint16_t tud_hid_get_report_cb(uint8_t instance, uint8_t report_id, hid_report_type_t report_type,
                               uint8_t *buffer, uint16_t reqlen)
{
  (void)instance;
  if (report_type == HID_REPORT_TYPE_FEATURE && report_id == REPORT_ID_MAX_COUNT && reqlen >= 1) {
    buffer[0] = TOUCH_MAX_CONTACTS;
    return 1;
  }
  return 0;
}

void tud_hid_set_report_cb(uint8_t instance, uint8_t report_id, hid_report_type_t report_type,
                           uint8_t const *buffer, uint16_t bufsize)
{
  (void)instance;
  (void)report_id;
  (void)report_type;
  (void)buffer;
  (void)bufsize;
}
