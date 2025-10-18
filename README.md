# VEILos4

VEILos4 is a lightweight embedded operating system designed for radio communication devices.

## Features

- **Minimal Footprint**: Designed for resource-constrained microcontrollers
- **Real-time Capable**: Simple task scheduler for embedded applications
- **Radio Support**: Built-in drivers for radio transceiver hardware
- **Modular Architecture**: Clean separation between bootloader, kernel, drivers, and applications

## Architecture

See [AGENTS.md](AGENTS.md) for detailed architecture documentation.

### Components

- **Bootloader**: Hardware initialization and kernel loading
- **Kernel**: Task scheduling, memory management, interrupt handling
- **Drivers**: Radio transceiver, UART, GPIO, timers
- **Applications**: Radio protocol stack and command interface

## Building

### Prerequisites

- ARM GCC toolchain (`arm-none-eabi-gcc`)
- GNU Make

### Build Commands

```bash
# Build the complete system
make

# Show build information
make info

# Clean build artifacts
make clean
```

### Build Output

The build system produces:
- `build/veilos4.elf` - ELF binary with debug symbols
- `build/veilos4.bin` - Raw binary for flashing

## Target Platform

VEILos4 targets ARM Cortex-M series microcontrollers with:
- Minimum 32KB RAM
- Minimum 128KB Flash
- Radio transceiver peripheral

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.