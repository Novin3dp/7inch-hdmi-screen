#ifndef GT915_H
#define GT915_H

#include <stdbool.h>
#include <stdint.h>

#define GT915_MAX_POINTS 5

struct gt915_point {
  uint8_t id;
  uint16_t x, y, size;
};

struct gt915_info {
  bool present;
  char product_id[5];
  uint8_t config_version;
  uint16_t x_max, y_max;
  uint32_t i2c_errors;
};

bool gt915_init(void);
int gt915_read(struct gt915_point *pts);
const struct gt915_info *gt915_info(void);

#endif
