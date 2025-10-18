/**
 * VEILos4 Radio Header
 * Radio driver interface definitions
 */

#ifndef RADIO_H
#define RADIO_H

#include <stdint.h>

// Radio initialization
void radio_init(void);
void radio_driver_init(void);

// Radio transmission functions
int radio_transmit(const uint8_t *data, uint16_t length);
int radio_receive(uint8_t *buffer, uint16_t max_length, uint16_t *received_length);
void radio_set_frequency(uint32_t freq_hz);

#endif // RADIO_H
