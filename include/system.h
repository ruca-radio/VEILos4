/**
 * VEILos4 System Header
 * Core system definitions and function declarations
 */

#ifndef SYSTEM_H
#define SYSTEM_H

#include <stdint.h>

// Bootloader functions
void reset_handler(void);
void hw_init(void);

// Kernel functions
void kernel_main(void);
void kernel_init(void);
int task_create(void (*task_func)(void), uint32_t *stack, uint8_t priority);
void scheduler_start(void);

// Driver initialization
void drivers_init(void);

#endif // SYSTEM_H
