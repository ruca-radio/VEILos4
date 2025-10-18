/**
 * VEILos4 Drivers Initialization
 * Initialize all hardware drivers
 */

#include "../include/uart.h"
#include "../include/radio.h"

/**
 * Initialize all drivers
 */
void drivers_init(void) {
    // Initialize UART for debugging
    uart_init(115200);
    uart_puts("VEILos4 Driver Init\r\n");
    
    // Initialize radio driver
    radio_driver_init();
    uart_puts("Radio driver initialized\r\n");
}
