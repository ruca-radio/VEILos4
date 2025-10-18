/**
 * VEILos4 Kernel
 * Core operating system functionality
 */

#include <stdint.h>
#include "../include/system.h"
#include "../include/radio.h"

// Task control block
typedef struct {
    uint32_t *stack_ptr;
    uint8_t state;
    uint8_t priority;
} tcb_t;

#define MAX_TASKS 8
static tcb_t tasks[MAX_TASKS];
static uint8_t current_task = 0;
static uint8_t num_tasks = 0;

/**
 * Kernel main entry point
 */
void kernel_main(void) {
    // Initialize kernel subsystems
    kernel_init();
    
    // Initialize drivers
    drivers_init();
    
    // Initialize radio stack
    radio_init();
    
    // Start scheduler
    scheduler_start();
    
    // Should never reach here
    while(1);
}

/**
 * Initialize kernel subsystems
 */
void kernel_init(void) {
    // Initialize task list
    for (int i = 0; i < MAX_TASKS; i++) {
        tasks[i].state = 0;
        tasks[i].priority = 0;
        tasks[i].stack_ptr = 0;
    }
    
    num_tasks = 0;
}

/**
 * Create a new task
 */
int task_create(void (*task_func)(void), uint32_t *stack, uint8_t priority) {
    if (num_tasks >= MAX_TASKS) {
        return -1;
    }
    
    tasks[num_tasks].stack_ptr = stack;
    tasks[num_tasks].state = 1; // Ready
    tasks[num_tasks].priority = priority;
    
    num_tasks++;
    return 0;
}

/**
 * Simple round-robin scheduler
 */
void scheduler_start(void) {
    // Enable system tick timer
    // In real implementation, configure SysTick for context switching
    
    while(1) {
        // Simple cooperative multitasking
        for (uint8_t i = 0; i < num_tasks; i++) {
            if (tasks[i].state == 1) {
                current_task = i;
                // Execute task (simplified)
            }
        }
    }
}
