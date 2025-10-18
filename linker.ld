/**
 * VEILos4 Linker Script
 * Memory layout for ARM Cortex-M4 microcontroller
 * 
 * Adjust FLASH and RAM sizes for your specific target hardware
 */

/* Memory regions - adjust these for your target MCU */
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

/* Stack size */
_stack_size = 4K;

/* Entry point */
ENTRY(reset_handler)

SECTIONS
{
    /* Vector table and code in FLASH */
    .text :
    {
        . = ALIGN(4);
        KEEP(*(.vectors))           /* Vector table */
        *(.text)                    /* Program code */
        *(.text*)
        *(.rodata)                  /* Read-only data */
        *(.rodata*)
        . = ALIGN(4);
        _etext = .;                 /* End of text section */
    } > FLASH

    /* Initialized data - copied from FLASH to RAM at startup */
    _data_load = LOADADDR(.data);
    .data : 
    {
        . = ALIGN(4);
        _data_start = .;            /* Start of data section in RAM */
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _data_end = .;              /* End of data section in RAM */
    } > RAM AT > FLASH

    /* Uninitialized data - zeroed at startup */
    .bss :
    {
        . = ALIGN(4);
        _bss_start = .;             /* Start of BSS section */
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _bss_end = .;               /* End of BSS section */
    } > RAM

    /* Stack - grows downward from end of RAM */
    .stack :
    {
        . = ALIGN(8);
        _stack_start = .;
        . = . + _stack_size;
        . = ALIGN(8);
        _stack_end = .;
    } > RAM

    /* Remove information from the standard libraries */
    /DISCARD/ :
    {
        libc.a ( * )
        libm.a ( * )
        libgcc.a ( * )
    }

    /* Kernel start marker */
    _kernel_start = ADDR(.text);
}
