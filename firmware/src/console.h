#ifndef CONSOLE_H
#define CONSOLE_H

void console_init(void);
void console_poll(void);
void console_printf(const char *fmt, ...) __attribute__((format(printf, 1, 2)));

#endif
