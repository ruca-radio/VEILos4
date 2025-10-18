/**
 * VEILos4 UART Header
 * UART driver interface definitions
 */

#ifndef UART_H
#define UART_H

#include <stdint.h>

// UART initialization and I/O functions
void uart_init(uint32_t baud_rate);
void uart_putc(char c);
void uart_puts(const char *str);
char uart_getc(void);

#endif // UART_H
