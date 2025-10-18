/**
 * VEILos4 Startup Code
 * Vector table and interrupt handlers
 */

#include <stdint.h>

// External symbols from linker script
extern uint32_t _stack_end;
extern void reset_handler(void);

// Default handler for unused interrupts
void default_handler(void) {
    while(1);
}

// Weak aliases for interrupt handlers
void NMI_Handler(void)              __attribute__((weak, alias("default_handler")));
void HardFault_Handler(void)        __attribute__((weak, alias("default_handler")));
void MemManage_Handler(void)        __attribute__((weak, alias("default_handler")));
void BusFault_Handler(void)         __attribute__((weak, alias("default_handler")));
void UsageFault_Handler(void)       __attribute__((weak, alias("default_handler")));
void SVC_Handler(void)              __attribute__((weak, alias("default_handler")));
void DebugMon_Handler(void)         __attribute__((weak, alias("default_handler")));
void PendSV_Handler(void)           __attribute__((weak, alias("default_handler")));
void SysTick_Handler(void)          __attribute__((weak, alias("default_handler")));

// External interrupt handlers (examples)
void WWDG_IRQHandler(void)          __attribute__((weak, alias("default_handler")));
void PVD_IRQHandler(void)           __attribute__((weak, alias("default_handler")));
void TAMP_STAMP_IRQHandler(void)    __attribute__((weak, alias("default_handler")));
void RTC_WKUP_IRQHandler(void)      __attribute__((weak, alias("default_handler")));
void FLASH_IRQHandler(void)         __attribute__((weak, alias("default_handler")));
void RCC_IRQHandler(void)           __attribute__((weak, alias("default_handler")));
void EXTI0_IRQHandler(void)         __attribute__((weak, alias("default_handler")));
void EXTI1_IRQHandler(void)         __attribute__((weak, alias("default_handler")));
void EXTI2_IRQHandler(void)         __attribute__((weak, alias("default_handler")));
void EXTI3_IRQHandler(void)         __attribute__((weak, alias("default_handler")));
void EXTI4_IRQHandler(void)         __attribute__((weak, alias("default_handler")));

/**
 * Vector table
 * Located at the start of FLASH memory
 */
__attribute__((section(".vectors")))
const void *vector_table[] = {
    &_stack_end,            // Initial stack pointer
    reset_handler,          // Reset handler
    NMI_Handler,            // NMI handler
    HardFault_Handler,      // Hard fault handler
    MemManage_Handler,      // Memory management fault
    BusFault_Handler,       // Bus fault handler
    UsageFault_Handler,     // Usage fault handler
    0,                      // Reserved
    0,                      // Reserved
    0,                      // Reserved
    0,                      // Reserved
    SVC_Handler,            // SVCall handler
    DebugMon_Handler,       // Debug monitor handler
    0,                      // Reserved
    PendSV_Handler,         // PendSV handler
    SysTick_Handler,        // SysTick handler
    
    // External interrupts (Cortex-M4 specific)
    WWDG_IRQHandler,        // Window Watchdog
    PVD_IRQHandler,         // PVD through EXTI Line detection
    TAMP_STAMP_IRQHandler,  // Tamper and TimeStamp
    RTC_WKUP_IRQHandler,    // RTC Wakeup
    FLASH_IRQHandler,       // FLASH
    RCC_IRQHandler,         // RCC
    EXTI0_IRQHandler,       // EXTI Line0
    EXTI1_IRQHandler,       // EXTI Line1
    EXTI2_IRQHandler,       // EXTI Line2
    EXTI3_IRQHandler,       // EXTI Line3
    EXTI4_IRQHandler,       // EXTI Line4
    // Add more interrupt handlers as needed for your target MCU
};
