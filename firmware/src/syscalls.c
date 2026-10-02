/* minimal newlib stubs (no file I/O on this target; console output uses console_printf) */
#include <sys/stat.h>
int _close(int fd) { (void)fd; return -1; }
int _lseek(int fd, int p, int d) { (void)fd; (void)p; (void)d; return 0; }
int _read(int fd, char *b, int n) { (void)fd; (void)b; (void)n; return 0; }
int _write(int fd, const char *b, int n) { (void)fd; (void)b; return n; }
int _fstat(int fd, struct stat *st) { (void)fd; st->st_mode = S_IFCHR; return 0; }
int _isatty(int fd) { (void)fd; return 1; }
