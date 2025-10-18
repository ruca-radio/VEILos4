# VEILos4 Build Guide

This document describes how to build VEILos4 from source.

## Prerequisites

### Required Tools

1. **ARM GCC Toolchain**
   - Package: `gcc-arm-none-eabi`
   - Version: 10.0 or later recommended
   - Download: https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm

2. **GNU Make**
   - Most Linux distributions include this by default
   - For Windows: Install via MSYS2 or Cygwin

### Installing the ARM Toolchain

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install gcc-arm-none-eabi binutils-arm-none-eabi
```

#### macOS:
```bash
brew install gcc-arm-embedded
```

#### Windows:
Download and install from ARM's official website:
https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm

## Building VEILos4

### Quick Start

```bash
# Clone the repository
git clone https://github.com/ruca-radio/VEILos4.git
cd VEILos4

# Build the system
make

# The output will be in the build/ directory
```

### Build Targets

- `make all` or `make`: Build the complete system
- `make clean`: Remove all build artifacts
- `make info`: Display build configuration and source files

### Build Output

The build process generates the following files in the `build/` directory:

- **veilos4.elf**: ELF executable with debug symbols (for debugging with GDB)
- **veilos4.bin**: Raw binary image (for flashing to microcontroller)
- **\*.o**: Object files (intermediate build artifacts)

## Flashing to Hardware

To flash the binary to your target hardware, use an appropriate tool:

### Using OpenOCD:
```bash
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
    -c "program build/veilos4.bin 0x08000000 verify reset exit"
```

### Using ST-Link:
```bash
st-flash write build/veilos4.bin 0x8000000
```

## Debugging

To debug VEILos4 with GDB:

```bash
# Start OpenOCD in one terminal
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg

# In another terminal, start GDB
arm-none-eabi-gdb build/veilos4.elf

# In GDB, connect to OpenOCD
(gdb) target remote localhost:3333
(gdb) monitor reset halt
(gdb) load
(gdb) continue
```

## Build Customization

### Changing Target MCU

Edit the `CFLAGS` in the Makefile to match your target:

```makefile
# For Cortex-M3
CFLAGS = -mcpu=cortex-m3 -mthumb

# For Cortex-M7 with FPU
CFLAGS = -mcpu=cortex-m7 -mthumb -mfloat-abi=hard -mfpu=fpv5-sp-d16
```

### Optimization Levels

The default optimization level is `-O2`. You can change this:

- `-O0`: No optimization (best for debugging)
- `-O1`: Basic optimization
- `-O2`: Recommended optimization (default)
- `-O3`: Aggressive optimization
- `-Os`: Optimize for size

## Troubleshooting

### Build Errors

**Error: arm-none-eabi-gcc: command not found**
- Solution: Install the ARM GCC toolchain as described above

**Error: undefined reference to `_data_start`**
- Solution: Create a linker script (see LINKER.md for details)

**Warning: unused parameter**
- This is expected for skeleton implementations
- These will be used as functionality is implemented

### Common Issues

1. **Build directory not created**
   - Solution: The Makefile creates this automatically, but ensure you have write permissions

2. **Compilation warnings**
   - Solution: Most warnings are informational and don't prevent building
   - Address them as the implementation is completed

## Additional Resources

- ARM Cortex-M Programming: https://www.arm.com/resources/education
- GNU Make Manual: https://www.gnu.org/software/make/manual/
- OpenOCD Documentation: http://openocd.org/documentation/
