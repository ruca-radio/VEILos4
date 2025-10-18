/**
 * VEILos4 UART Driver
 * Driver for serial communication
 */

#include <stdint.h>
#include "../include/uart.h"

// UART hardware registers (placeholder addresses)
#define UART_BASE       0x40001000
#define UART_DATA       ((volatile uint32_t*)(UART_BASE + 0x00))
#define UART_STATUS     ((volatile uint32_t*)(UART_BASE + 0x04))
#define UART_CTRL       ((volatile uint32_t*)(UART_BASE + 0x08))
#define UART_BAUD       ((volatile uint32_t*)(UART_BASE + 0x0C))

/**
 * Initialize UART
 */
void uart_init(uint32_t baud_rate) {
    // Set baud rate
    *UART_BAUD = baud_rate;
    
    // Enable UART TX and RX
    *UART_CTRL = 0x00000003;
}

/**
 * Send byte via UART
 */
void uart_putc(char c) {
    // Wait for TX ready
    while ((*UART_STATUS & 0x01) == 0);
    
    // Write data
    *UART_DATA = c;
}

/**
 * Send string via UART
 */
void uart_puts(const char *str) {
    while (*str) {
        uart_putc(*str++);
    }
}

/**
 * Receive byte from UART
 */
char uart_getc(void) {
    // Wait for RX data available
    while ((*UART_STATUS & 0x02) == 0);
    
    // Read data
    return *UART_DATA & 0xFF;
}
