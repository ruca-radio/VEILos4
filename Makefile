# VEILos4 Makefile
# Build system for VEILos4 embedded operating system

# Target configuration
TARGET = veilos4

# Toolchain
CC = arm-none-eabi-gcc
AS = arm-none-eabi-as
LD = arm-none-eabi-ld
OBJCOPY = arm-none-eabi-objcopy
SIZE = arm-none-eabi-size

# Directories
BUILD_DIR = build
BOOTLOADER_DIR = bootloader
KERNEL_DIR = kernel
DRIVERS_DIR = drivers
APPS_DIR = apps
INCLUDE_DIR = include

# Compiler flags
CFLAGS = -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16
CFLAGS += -O2 -g -Wall -Wextra
CFLAGS += -I$(INCLUDE_DIR)
CFLAGS += -ffunction-sections -fdata-sections

# Linker flags
LDFLAGS = -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16
LDFLAGS += -Wl,--gc-sections
LDFLAGS += -T linker.ld
LDFLAGS += -nostartfiles

# Source files
BOOTLOADER_SRCS = $(wildcard $(BOOTLOADER_DIR)/*.c)
KERNEL_SRCS = $(wildcard $(KERNEL_DIR)/*.c)
DRIVERS_SRCS = $(wildcard $(DRIVERS_DIR)/*.c)
APPS_SRCS = $(wildcard $(APPS_DIR)/*.c)

ALL_SRCS = $(BOOTLOADER_SRCS) $(KERNEL_SRCS) $(DRIVERS_SRCS) $(APPS_SRCS)

# Object files
OBJS = $(patsubst %.c,$(BUILD_DIR)/%.o,$(notdir $(ALL_SRCS)))

# Default target
all: $(BUILD_DIR) $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).bin

# Create build directory
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

# Compile source files
$(BUILD_DIR)/%.o: $(BOOTLOADER_DIR)/%.c
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD_DIR)/%.o: $(KERNEL_DIR)/%.c
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD_DIR)/%.o: $(DRIVERS_DIR)/%.c
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD_DIR)/%.o: $(APPS_DIR)/%.c
	@echo "Compiling $<"
	$(CC) $(CFLAGS) -c $< -o $@

# Link
$(BUILD_DIR)/$(TARGET).elf: $(OBJS)
	@echo "Linking $@"
	$(CC) $(LDFLAGS) -o $@ $(OBJS)
	$(SIZE) $@

# Create binary
$(BUILD_DIR)/$(TARGET).bin: $(BUILD_DIR)/$(TARGET).elf
	@echo "Creating binary $@"
	$(OBJCOPY) -O binary $< $@

# Clean
clean:
	@echo "Cleaning build directory"
	@rm -rf $(BUILD_DIR)

# Phony targets
.PHONY: all clean

# Info target
info:
	@echo "VEILos4 Build System"
	@echo "===================="
	@echo "Target: $(TARGET)"
	@echo "Toolchain: $(CC)"
	@echo ""
	@echo "Source files:"
	@echo "  Bootloader: $(BOOTLOADER_SRCS)"
	@echo "  Kernel: $(KERNEL_SRCS)"
	@echo "  Drivers: $(DRIVERS_SRCS)"
	@echo "  Apps: $(APPS_SRCS)"
	@echo ""
	@echo "Build directory: $(BUILD_DIR)"
	@echo ""
	@echo "Available targets:"
	@echo "  all     - Build the complete system"
	@echo "  clean   - Remove build artifacts"
	@echo "  info    - Show this information"
