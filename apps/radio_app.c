/**
 * VEILos4 Radio Application
 * Radio protocol stack and command interface
 */

#include <stdint.h>
#include "../include/radio.h"
#include "../include/uart.h"

// Radio protocol states
typedef enum {
    RADIO_STATE_IDLE = 0,
    RADIO_STATE_RX,
    RADIO_STATE_TX
} radio_state_t;

static radio_state_t radio_state = RADIO_STATE_IDLE;

/**
 * Initialize radio application
 */
void radio_init(void) {
    uart_puts("Radio app initialized\r\n");
    radio_state = RADIO_STATE_IDLE;
}

/**
 * Radio application main loop
 */
void radio_task(void) {
    uint8_t rx_buffer[256];
    uint16_t rx_length;
    
    while (1) {
        switch (radio_state) {
            case RADIO_STATE_IDLE:
                // Wait for commands
                break;
                
            case RADIO_STATE_RX:
                // Check for received data
                if (radio_receive(rx_buffer, sizeof(rx_buffer), &rx_length) == 0) {
                    if (rx_length > 0) {
                        // Process received data
                        uart_puts("Data received\r\n");
                    }
                }
                break;
                
            case RADIO_STATE_TX:
                // Handle transmission
                break;
        }
    }
}

/**
 * Send message via radio
 */
int radio_send_message(const uint8_t *message, uint16_t length) {
    radio_state = RADIO_STATE_TX;
    int result = radio_transmit(message, length);
    radio_state = RADIO_STATE_IDLE;
    return result;
}
