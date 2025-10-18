/**
 * VEILos4 Bootloader
 * Initializes hardware and loads the kernel
 */

#include <stdint.h>
#include "../include/system.h"

// External symbol from linker script
extern uint32_t _kernel_start;
extern void kernel_main(void);

/**
 * Reset handler - entry point after reset
 */
void reset_handler(void) {
    // Initialize data section
    extern uint32_t _data_start, _data_end, _data_load;
    uint32_t *src = &_data_load;
    uint32_t *dst = &_data_start;
    
    while (dst < &_data_end) {
        *dst++ = *src++;
    }
    
    // Zero BSS section
    extern uint32_t _bss_start, _bss_end;
    dst = &_bss_start;
    
    while (dst < &_bss_end) {
        *dst++ = 0;
    }
    
    // Initialize hardware
    hw_init();
    
    // Jump to kernel
    kernel_main();
    
    // Should never reach here
    while(1);
}

/**
 * Initialize basic hardware
 */
void hw_init(void) {
    // Enable FPU if present
    #ifdef __ARM_FP
    uint32_t *cpacr = (uint32_t *)0xE000ED88;
    *cpacr |= (0xF << 20);
    #endif
    
    // Initialize system clock (placeholder)
    // In real implementation, configure PLL and clocks
    
    // Initialize interrupts (placeholder)
    // In real implementation, set up NVIC
}
