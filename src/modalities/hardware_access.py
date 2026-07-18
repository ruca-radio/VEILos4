"""
Hardware Access Module

This module provides interfaces for accessing and optimizing hardware resources
such as CPU, GPU, and memory, with support for performance monitoring and
dynamic resource allocation.
"""

# import importlib  # Unused import
# import json  # Unused import
import logging
import platform
import re
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional

# Logger for the module
logger = logging.getLogger(__name__)


class HardwareAccessError(Exception):
    """Base exception for hardware access related errors"""


class ResourceUnavailableError(HardwareAccessError):
    """Exception raised when a hardware resource is unavailable"""


class ResourceLimitExceededError(HardwareAccessError):
    """Exception raised when hardware resource limits are exceeded"""


class DriverNotFoundError(HardwareAccessError):
    """Exception raised when required hardware drivers are not found"""

    pass


class HardwareType(Enum):
    """Enumeration for hardware types."""

    CPU = auto()
    GPU = auto()
    TPU = auto()
    MEMORY = auto()
    DISK = auto()
    NETWORK = auto()


class GPUVendor(Enum):
    """Enumeration for GPU vendors."""

    NVIDIA = auto()
    AMD = auto()
    INTEL = auto()
    APPLE = auto()
    OTHER = auto()
    UNKNOWN = auto()


class CPUArchitecture(Enum):
    """CPU architecture types"""

    X86 = auto()
    X86_64 = auto()
    ARM = auto()
    ARM64 = auto()
    RISC_V = auto()
    POWER = auto()
    UNKNOWN = auto()

    @classmethod
    def detect(cls) -> "CPUArchitecture":
        """Detect the current CPU architecture"""
        machine = platform.machine().lower()

        if machine in ("x86_64", "amd64"):
            return cls.X86_64
        if machine in ("i386", "i686", "x86"):
            return cls.X86
        if machine in ("arm64", "aarch64"):
            return cls.ARM64
        if machine.startswith("arm"):
            return cls.ARM
        if machine.startswith("riscv"):
            return cls.RISC_V
        if machine.startswith("ppc") or machine.startswith("power"):
            return cls.POWER
        return cls.UNKNOWN
        return cls.UNKNOWN


class AcceleratorType(Enum):
    """Types of hardware accelerators"""

    CUDA = auto()
    ROCM = auto()
    MPS = auto()
    OPENCL = auto()
    VULKAN = auto()
    METAL = auto()
    DIRECTML = auto()
    UNKNOWN = auto()


class MemoryType(Enum):
    """Types of memory"""

    RAM = auto()
    VRAM = auto()
    SWAP = auto()
    UNIFIED = auto()


class OptimizationLevel(Enum):
    """Optimization levels for hardware resource usage"""

    NONE = 0
    MINIMAL = 1
    BALANCED = 2
    AGGRESSIVE = 3
    MAXIMUM = 4


class MetricType(Enum):
    """Types of hardware performance metrics"""

    UTILIZATION = auto()  # Percentage utilization
    TEMPERATURE = auto()  # Temperature in degrees Celsius
    POWER = auto()  # Power consumption in watts
    MEMORY_USAGE = auto()  # Memory usage in bytes
    CLOCK_SPEED = auto()  # Clock speed in MHz
    THROUGHPUT = auto()  # Operations per second
    LATENCY = auto()  # Response time in milliseconds


@dataclass
class HardwareCapabilities:
    """Base class for hardware capabilities information"""

    hardware_type: HardwareType
    available: bool = True
    vendor: str = "Unknown"
    model: str = "Unknown"
    driver_version: Optional[str] = None
    total_memory: Optional[int] = None  # in bytes

    def to_dict(self) -> Dict[str, Any]:
        """Convert capabilities to a dictionary"""
        return {
            "hardware_type": self.hardware_type.name,
            "available": self.available,
            "vendor": self.vendor,
            "model": self.model,
            "driver_version": self.driver_version,
            "total_memory": self.total_memory,
        }


@dataclass
class CPUCapabilities(HardwareCapabilities):
    """CPU capabilities information"""

    architecture: CPUArchitecture = CPUArchitecture.UNKNOWN
    cores: int = 0
    threads_per_core: int = 0
    frequency_mhz: float = 0.0
    cache_size: Optional[int] = None  # in bytes
    features: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.hardware_type = HardwareType.CPU

    def to_dict(self) -> Dict[str, Any]:
        """Convert CPU capabilities to a dictionary"""
        base_dict = super().to_dict()
        cpu_dict = {
            "architecture": self.architecture.name,
            "cores": self.cores,
            "threads_per_core": self.threads_per_core,
            "frequency_mhz": self.frequency_mhz,
            "cache_size": self.cache_size,
            "features": self.features,
        }
        return {**base_dict, **cpu_dict}


@dataclass
class GPUCapabilities(HardwareCapabilities):
    """GPU capabilities information"""

    gpu_vendor: GPUVendor = GPUVendor.UNKNOWN
    accelerator_type: AcceleratorType = AcceleratorType.UNKNOWN
    compute_units: int = 0
    cuda_cores: Optional[int] = None
    tensor_cores: Optional[int] = None
    vram: Optional[int] = None  # in bytes
    shared_memory: bool = False
    max_power_draw: Optional[float] = None  # in watts
    supported_precisions: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.hardware_type = HardwareType.GPU

    def to_dict(self) -> Dict[str, Any]:
        """Convert GPU capabilities to a dictionary"""
        base_dict = super().to_dict()
        gpu_dict = {
            "gpu_vendor": self.gpu_vendor.name,
            "accelerator_type": self.accelerator_type.name,
            "compute_units": self.compute_units,
            "cuda_cores": self.cuda_cores,
            "tensor_cores": self.tensor_cores,
            "vram": self.vram,
            "shared_memory": self.shared_memory,
            "max_power_draw": self.max_power_draw,
            "supported_precisions": self.supported_precisions,
        }
        return {**base_dict, **gpu_dict}


@dataclass
class MemoryCapabilities(HardwareCapabilities):
    """Memory capabilities information"""

    memory_type: MemoryType = MemoryType.RAM
    total_capacity: int = 0  # in bytes
    available: int = 0  # in bytes
    speed_mhz: Optional[float] = None
    channels: Optional[int] = None
    page_size: Optional[int] = None  # in bytes

    def __post_init__(self):
        self.hardware_type = HardwareType.MEMORY

    def to_dict(self) -> Dict[str, Any]:
        """Convert memory capabilities to a dictionary"""
        base_dict = super().to_dict()
        memory_dict = {
            "memory_type": self.memory_type.name,
            "total_capacity": self.total_capacity,
            "available": self.available,
            "speed_mhz": self.speed_mhz,
            "channels": self.channels,
            "page_size": self.page_size,
        }
        return {**base_dict, **memory_dict}


@dataclass
class PerformanceMetric:
    """Performance metric data"""

    metric_type: MetricType
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    device_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to a dictionary"""
        return {
            "metric_type": self.metric_type.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "device_id": self.device_id,
        }


@dataclass
class ResourceAllocation:
    """Resource allocation configuration"""

    hardware_type: HardwareType
    device_id: Optional[str] = None
    memory_limit: Optional[int] = None  # in bytes
    compute_limit: Optional[float] = None  # percentage (0-100)
    priority: int = 0  # Higher number means higher priority
    exclusive: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert allocation to a dictionary"""
        return {
            "hardware_type": self.hardware_type.name,
            "device_id": self.device_id,
            "memory_limit": self.memory_limit,
            "compute_limit": self.compute_limit,
            "priority": self.priority,
            "exclusive": self.exclusive,
        }


class HardwareResource(ABC):
    """
    Abstract base class for hardware resources.
    """

    @property
    @abstractmethod
    def hardware_type(self) -> HardwareType:
        """Get the type of hardware resource."""
        pass

    @property
    @abstractmethod
    def available(self) -> bool:
        """Check if the resource is available."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> HardwareCapabilities:
        """Get the capabilities of this resource."""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, PerformanceMetric]:
        """
        Get current performance metrics for the resource.

        Returns:
            Dictionary mapping metric names to PerformanceMetric objects
        """
        pass

    @abstractmethod
    def allocate(self, allocation: ResourceAllocation) -> bool:
        """
        Allocate this resource according to the specified configuration.

        Args:
            allocation: Resource allocation configuration

        Returns:
            True if allocation was successful, False otherwise
        """
        pass

    @abstractmethod
    def release(self) -> None:
        """Release this resource."""
        pass

    def __init__(self, device_id: Optional[str] = None):
        self._device_id = device_id or "0"
        self._available = False
        self._allocation: Optional[ResourceAllocation] = None
        self._lock = threading.RLock()
        self._capabilities = self._detect_capabilities()
        self._available = self._capabilities.available

    @property
    def hardware_type(self) -> HardwareType:
        return HardwareType.GPU

    @property
    def available(self) -> bool:
        with self._lock:
            return self._available

    @property
    def capabilities(self) -> GPUCapabilities:
        return self._capabilities

    def _detect_capabilities(self) -> GPUCapabilities:
        caps = GPUCapabilities(
            hardware_type=HardwareType.GPU,
            available=False,
            gpu_vendor=GPUVendor.UNKNOWN,
            accelerator_type=AcceleratorType.UNKNOWN,
        )
        try:
            if self._detect_nvidia_gpu(caps):
                return caps
            if self._detect_amd_gpu(caps):
                return caps
            if self._detect_intel_gpu(caps):
                return caps
            if self._detect_apple_gpu(caps):
                return caps
            if self._detect_ml_framework_gpu(caps):
                return caps
            logger.info("No GPU detected or supported")
            return caps
        except Exception as e:
            logger.error(f"Error detecting GPU capabilities: {str(e)}")
            return caps

    def _detect_nvidia_gpu(self, caps: GPUCapabilities) -> bool:
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,driver_version,memory.total,compute_cap",
                    "--format=csv,noheader",
                ],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                gpu_info = result.stdout.strip().split(",")
                if len(gpu_info) >= 4:
                    caps.available = True
                    caps.gpu_vendor = GPUVendor.NVIDIA
                    caps.accelerator_type = AcceleratorType.CUDA
                    caps.model = gpu_info[0].strip()
                    caps.vendor = "NVIDIA"
                    caps.driver_version = gpu_info[1].strip()
                    memory_str = gpu_info[2].strip()
                    if "MiB" in memory_str:
                        memory_mib = int(memory_str.split(" ")[0])
                        caps.vram = memory_mib * 1024 * 1024
                        caps.total_memory = caps.vram
                    # Try to get CUDA details
                    if torch and torch.cuda.is_available():
                        caps.cuda_cores = None  # Not easily available
                        caps.tensor_cores = None  # Not easily available
                        caps.supported_precisions = ["float16", "float32", "float64"]
                    # Power info
                    power_result = subprocess.run(
                        [
                            "nvidia-smi",
                            "--query-gpu=power.limit",
                            "--format=csv,noheader",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=1.0,
                        check=False,
                    )
                    if power_result.returncode == 0 and power_result.stdout:
                        try:
                            caps.max_power_draw = float(
                                power_result.stdout.strip().split()[0]
                            )
                        except Exception:
                            pass
                    return True
        except (subprocess.SubprocessError, FileNotFoundError, Exception):
            pass
        # Try PyTorch
        if (
            torch
            and torch.cuda.is_available()
            and torch.cuda.device_count() > int(self._device_id)
        ):
            caps.available = True
            caps.gpu_vendor = GPUVendor.NVIDIA
            caps.accelerator_type = AcceleratorType.CUDA
            caps.model = torch.cuda.get_device_name(int(self._device_id))
            caps.vendor = "NVIDIA"


try:
    import torch
except ImportError:
    torch = None

try:
    import tensorflow as tf
except ImportError:
    try:
        import tensorflow as tf
    except ImportError:
        tf = None


class GPU(HardwareResource):
    """
    GPU hardware resource.
    """

    def __init__(self, device_id: Optional[str] = None):
        super().__init__(device_id)
        self._available = False
        self._allocation: Optional[ResourceAllocation] = None
        self._lock = threading.RLock()
        self._capabilities = self._detect_capabilities()
        self._available = self._capabilities.available

    @property
    def hardware_type(self) -> HardwareType:
        return HardwareType.GPU

    @property
    def available(self) -> bool:
        with self._lock:
            return self._available

    @property
    def capabilities(self) -> GPUCapabilities:
        return self._capabilities

    def _detect_capabilities(self) -> GPUCapabilities:
        caps = GPUCapabilities(
            hardware_type=HardwareType.GPU,
            available=False,
            gpu_vendor=GPUVendor.UNKNOWN,
            accelerator_type=AcceleratorType.UNKNOWN,
        )
        try:
            if self._detect_nvidia_gpu(caps):
                return caps
            if self._detect_amd_gpu(caps):
                return caps
            if self._detect_intel_gpu(caps):
                return caps
            if self._detect_apple_gpu(caps):
                return caps
            if self._detect_ml_framework_gpu(caps):
                return caps
            logger.info("No GPU detected or supported")
            return caps
        except Exception as e:
            logger.error("Error detecting GPU capabilities: %s", str(e))
            return caps

    def _detect_nvidia_gpu(self, caps: GPUCapabilities) -> bool:
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,driver_version,memory.total,compute_cap",
                    "--format=csv,noheader",
                ],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                gpu_info = result.stdout.strip().split(",")
                if len(gpu_info) >= 4:
                    caps.available = True
                    caps.gpu_vendor = GPUVendor.NVIDIA
                    caps.accelerator_type = AcceleratorType.CUDA
                    caps.model = gpu_info[0].strip()
                    caps.vendor = "NVIDIA"
                    caps.driver_version = gpu_info[1].strip()
                    memory_str = gpu_info[2].strip()
                    if "MiB" in memory_str:
                        memory_mib = int(memory_str.split(" ")[0])
                        caps.vram = memory_mib * 1024 * 1024
                        caps.total_memory = caps.vram
                    # Try to get CUDA details
                    if torch and torch.cuda.is_available():
                        caps.cuda_cores = None  # Not easily available
                        caps.tensor_cores = None  # Not easily available
                        caps.supported_precisions = ["float16", "float32", "float64"]
                    # Power info
                    power_result = subprocess.run(
                        [
                            "nvidia-smi",
                            "--query-gpu=power.limit",
                            "--format=csv,noheader",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=1.0,
                        check=False,
                    )
                    if power_result.returncode == 0 and power_result.stdout:
                        try:
                            caps.max_power_draw = float(
                                power_result.stdout.strip().split()[0]
                            )
                        except Exception:
                            pass
                    return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        # Try PyTorch
        if (
            torch
            and torch.cuda.is_available()
            and torch.cuda.device_count() > int(self._device_id)
        ):
            caps.available = True
            caps.gpu_vendor = GPUVendor.NVIDIA
            caps.accelerator_type = AcceleratorType.CUDA
            caps.model = torch.cuda.get_device_name(int(self._device_id))
            caps.vendor = "NVIDIA"
            caps.vram = torch.cuda.get_device_properties(
                int(self._device_id)
            ).total_memory
            caps.total_memory = caps.vram
            caps.supported_precisions = ["float16", "float32", "float64"]
            return True
        # Try TensorFlow
        if tf:
            gpus = tf.config.list_physical_devices("GPU")
            if len(gpus) > int(self._device_id):
                caps.available = True
                caps.gpu_vendor = GPUVendor.NVIDIA
                caps.accelerator_type = AcceleratorType.CUDA
                caps.model = gpus[int(self._device_id)].name
                caps.vendor = "NVIDIA"
                caps.supported_precisions = ["float16", "float32", "float64"]
                return True
        return False

    def _detect_amd_gpu(self, caps: GPUCapabilities) -> bool:
        try:
            result = subprocess.run(
                ["rocm-smi", "--showproductname", "--showvram"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split("\n")
                product_line = next(
                    (line for line in lines if "Product name" in line), ""
                )
                if product_line:
                    model = product_line.split(":")[-1].strip()
                    caps.model = model
                    caps.vendor = "AMD"
                    caps.gpu_vendor = GPUVendor.AMD
                    caps.accelerator_type = AcceleratorType.ROCM
                    caps.available = True
                vram_line = next((line for line in lines if "VRAM" in line), "")
                if vram_line:
                    try:
                        vram_gb = float(vram_line.split(":")[-1].strip().split()[0])
                        caps.vram = int(vram_gb * 1024 * 1024 * 1024)
                        caps.total_memory = caps.vram
                    except Exception:
                        pass
                return caps.available
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return False

    def _detect_intel_gpu(self, caps: GPUCapabilities) -> bool:
        if platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["lspci"], capture_output=True, text=True, timeout=2.0, check=False
                )
                if result.returncode == 0 and result.stdout:
                    if "Intel" in result.stdout and "VGA" in result.stdout:
                        caps.model = "Intel Integrated Graphics"
                        caps.vendor = "Intel"
                        caps.gpu_vendor = GPUVendor.INTEL
                        caps.accelerator_type = AcceleratorType.UNKNOWN
                        caps.available = True
                        return True
            except Exception:
                pass
        elif platform.system() == "Windows":
            # Not implemented
            pass
        return False

    def _detect_apple_gpu(self, caps: GPUCapabilities) -> bool:
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                    check=False,
                )
                if result.returncode == 0 and result.stdout:
                    if "Apple" in result.stdout:
                        caps.model = "Apple GPU"
                        caps.vendor = "Apple"
                        caps.gpu_vendor = GPUVendor.APPLE
                        caps.accelerator_type = AcceleratorType.METAL
                        caps.available = True
                        return True
            except Exception:
                pass
        return False

    def _detect_ml_framework_gpu(self, caps: GPUCapabilities) -> bool:
        # Fallback: check ML frameworks
        if torch and torch.cuda.is_available():
            caps.available = True
            caps.gpu_vendor = GPUVendor.NVIDIA
            caps.accelerator_type = AcceleratorType.CUDA
            caps.model = torch.cuda.get_device_name(int(self._device_id))
            caps.vendor = "NVIDIA"
            caps.vram = torch.cuda.get_device_properties(
                int(self._device_id)
            ).total_memory
            caps.total_memory = caps.vram
            caps.supported_precisions = ["float16", "float32", "float64"]
            return True
        if tf:
            gpus = tf.config.list_physical_devices("GPU")
            if len(gpus) > int(self._device_id):
                caps.available = True
                caps.gpu_vendor = GPUVendor.NVIDIA
                caps.accelerator_type = AcceleratorType.CUDA
                caps.model = gpus[int(self._device_id)].name
                caps.vendor = "NVIDIA"
                caps.supported_precisions = ["float16", "float32", "float64"]
                return True
        return False

    def get_metrics(self) -> Dict[str, PerformanceMetric]:
        metrics = {}
        # Example: utilization, memory usage, temperature
        try:
            if torch and torch.cuda.is_available():
                device_id = int(self._device_id)
                utilization = (
                    torch.cuda.utilization(device_id)
                    if hasattr(torch.cuda, "utilization")
                    else 0.0
                )
                metrics["utilization"] = PerformanceMetric(
                    metric_type=MetricType.UTILIZATION,
                    value=utilization,
                    unit="%",
                    device_id=self._device_id,
                )
                mem_alloc = torch.cuda.memory_allocated(device_id)
                metrics["memory_usage"] = PerformanceMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=mem_alloc,
                    unit="bytes",
                    device_id=self._device_id,
                )
        except Exception:
            pass
        return metrics

    def allocate(self, allocation: ResourceAllocation) -> bool:
        """
        Allocate GPU resources according to the specified configuration.

        Args:
            allocation: Resource allocation configuration

        Returns:
            True if allocation was successful, False otherwise
        """
        if allocation.hardware_type != HardwareType.GPU:
            logger.error("Cannot allocate %s resource to GPU", allocation.hardware_type)
            return False

        with self._lock:
            if not self._available:
                logger.warning("GPU resource not available")
                return False
            self._allocation = allocation
            logger.info("Allocated GPU resource with limits: %s", allocation)
            return True

    def release(self) -> None:
        with self._lock:
            if self._allocation:
                logger.info("Released GPU resource")
                self._allocation = None

    def _detect_amd_gpu(self, caps: GPUCapabilities) -> bool:
        try:
            result = subprocess.run(
                ["rocm-smi", "--showproductname", "--showvram"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split("\n")
                product_line = next(
                    (line for line in lines if "Product name" in line), ""
                )
                if product_line:
                    model = product_line.split(":")[-1].strip()
                    caps.model = model
                    caps.vendor = "AMD"
                    caps.gpu_vendor = GPUVendor.AMD
                    caps.accelerator_type = AcceleratorType.ROCM
                    caps.available = True
                vram_line = next((line for line in lines if "VRAM" in line), "")
                if vram_line:
                    try:
                        vram_gb = float(vram_line.split(":")[-1].strip().split()[0])
                        caps.vram = int(vram_gb * 1024 * 1024 * 1024)
                        caps.total_memory = caps.vram
                    except Exception:
                        pass
                return caps.available
        except (subprocess.SubprocessError, FileNotFoundError, Exception):
            pass
        return False

    def _detect_intel_gpu(self, caps: GPUCapabilities) -> bool:
        if platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["lspci"], capture_output=True, text=True, timeout=2.0
                )
                if result.returncode == 0 and result.stdout:
                    if "Intel" in result.stdout and "VGA" in result.stdout:
                        caps.model = "Intel Integrated Graphics"
                        caps.vendor = "Intel"
                        caps.gpu_vendor = GPUVendor.INTEL
                        caps.accelerator_type = AcceleratorType.UNKNOWN
                        caps.available = True
                        return True
            except Exception:
                pass
        elif platform.system() == "Windows":
            # Not implemented
            pass
        return False

    def _detect_apple_gpu(self, caps: GPUCapabilities) -> bool:
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
                if result.returncode == 0 and result.stdout:
                    if "Apple" in result.stdout:
                        caps.model = "Apple GPU"
                        caps.vendor = "Apple"
                        caps.gpu_vendor = GPUVendor.APPLE
                        caps.accelerator_type = AcceleratorType.METAL
                        caps.available = True
                        return True
            except Exception:
                pass
        return False

    def _detect_ml_framework_gpu(self, caps: GPUCapabilities) -> bool:
        # Fallback: check ML frameworks
        if torch and torch.cuda.is_available():
            caps.available = True
            caps.gpu_vendor = GPUVendor.NVIDIA
            caps.accelerator_type = AcceleratorType.CUDA
            caps.model = torch.cuda.get_device_name(int(self._device_id))
            caps.vendor = "NVIDIA"
            caps.vram = torch.cuda.get_device_properties(
                int(self._device_id)
            ).total_memory
            caps.total_memory = caps.vram
            caps.supported_precisions = ["float16", "float32", "float64"]
            return True
        if tf:
            gpus = tf.config.list_physical_devices("GPU")
            if len(gpus) > int(self._device_id):
                caps.available = True
                caps.gpu_vendor = GPUVendor.NVIDIA
                caps.accelerator_type = AcceleratorType.CUDA
                caps.model = gpus[int(self._device_id)].name
                caps.vendor = "NVIDIA"
                caps.supported_precisions = ["float16", "float32", "float64"]
                return True
        return False

    def get_metrics(self) -> Dict[str, PerformanceMetric]:
        metrics = {}
        # Example: utilization, memory usage, temperature
        try:
            if torch and torch.cuda.is_available():
                device_id = int(self._device_id)
                utilization = (
                    torch.cuda.utilization(device_id)
                    if hasattr(torch.cuda, "utilization")
                    else 0.0
                )
                metrics["utilization"] = PerformanceMetric(
                    metric_type=MetricType.UTILIZATION,
                    value=utilization,
                    unit="%",
                    device_id=self._device_id,
                )
                mem_alloc = torch.cuda.memory_allocated(device_id)
                metrics["memory_usage"] = PerformanceMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=mem_alloc,
                    unit="bytes",
                    device_id=self._device_id,
                )
        except Exception:
            pass
        return metrics

    def allocate(self, allocation: ResourceAllocation) -> bool:
        """
        Allocate GPU resources according to the specified configuration.

        Args:
            allocation: Resource allocation configuration

        Returns:
            True if allocation was successful, False otherwise
        """
        if allocation.hardware_type != HardwareType.GPU:
            logger.error(f"Cannot allocate {allocation.hardware_type} resource to GPU")
            return False

        with self._lock:
            if not self._available:
                logger.warning("GPU resource not available")
                return False
            self._allocation = allocation
            logger.info(f"Allocated GPU resource with limits: {allocation}")
            return True

    def release(self) -> None:
        with self._lock:
            if self._allocation:
                logger.info("Released GPU resource")
                self._allocation = None


class Memory(HardwareResource):
    def __init__(self, device_id: Optional[str] = None):
        self._device_id = device_id or "0"
        self._available = True
        self._allocation: Optional[ResourceAllocation] = None
        self._lock = threading.RLock()
        self._capabilities = self._detect_capabilities()

    @property
    def hardware_type(self) -> HardwareType:
        return HardwareType.MEMORY

    @property
    def available(self) -> bool:
        with self._lock:
            return self._available

    @property
    def capabilities(self) -> MemoryCapabilities:
        return self._capabilities

    def _detect_capabilities(self) -> MemoryCapabilities:
        caps = MemoryCapabilities(
            hardware_type=HardwareType.MEMORY,
            available=0,
            total_capacity=0,
            memory_type=MemoryType.RAM,
        )
        try:
            if platform.system() == "Linux":
                self._detect_linux_memory(caps)
            elif platform.system() == "Darwin":
                self._detect_macos_memory(caps)
            elif platform.system() == "Windows":
                self._detect_windows_memory(caps)
        except Exception as e:
            logger.warning(f"Error detecting memory info: {str(e)}")
        return caps

    def _detect_linux_memory(self, caps: MemoryCapabilities) -> None:
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
            total_match = re.search(r"MemTotal:\s+(\d+) kB", meminfo)
            free_match = re.search(r"MemAvailable:\s+(\d+) kB", meminfo)
            if total_match:
                caps.total_capacity = int(total_match.group(1)) * 1024
            if free_match:
                caps.available = int(free_match.group(1)) * 1024
        except Exception as e:
            logger.warning(f"Error parsing Linux memory info: {str(e)}")

    def _detect_macos_memory(self, caps: MemoryCapabilities) -> None:
        try:
            total_bytes = int(
                subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip()
            )
            caps.total_capacity = total_bytes
            caps.available = total_bytes  # macOS does not provide available easily
        except Exception as e:
            logger.warning(f"Error parsing macOS memory info: {str(e)}")

    def _detect_windows_memory(self, caps: MemoryCapabilities) -> None:
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            caps.total_capacity = stat.ullTotalPhys
            caps.available = stat.ullAvailPhys
        except Exception as e:
            logger.warning(f"Error parsing Windows memory info: {str(e)}")

    def get_metrics(self) -> Dict[str, PerformanceMetric]:
        metrics = {}
        try:
            # Try to use psutil if available
            import psutil

            # Different metrics based on memory type
            if self._memory_type == MemoryType.RAM:
                vm = psutil.virtual_memory()

                # Total memory
                metrics["total"] = PerformanceMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=float(vm.total),
                    unit="bytes (total)",
                    device_id="system",
                )

                # Used memory
                metrics["used"] = PerformanceMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=float(vm.used),
                    unit="bytes (used)",
                    device_id="system",
                )

                # Available memory
                metrics["available"] = PerformanceMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=float(vm.available),
                    unit="bytes (available)",
                    device_id="system",
                )

                # Utilization percentage
                metrics["utilization"] = PerformanceMetric(
                    metric_type=MetricType.UTILIZATION,
                    value=vm.percent,
                    unit="%",
                    device_id="system",
                )

            elif self._memory_type == MemoryType.SWAP:
                swap = psutil.swap_memory()

                # Total swap
                metrics["total"] = PerformanceMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=float(swap.total),
                    unit="bytes (total)",
                    device_id="swap",
                )

                # Used swap
                metrics["used"] = PerformanceMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=float(swap.used),
                    unit="bytes (used)",
                    device_id="swap",
                )

                # Free swap
                metrics["free"] = PerformanceMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=float(swap.free),
                    unit="bytes (free)",
                    device_id="swap",
                )

                # Utilization percentage
                metrics["utilization"] = PerformanceMetric(
                    metric_type=MetricType.UTILIZATION,
                    value=swap.percent,
                    unit="%",
                    device_id="swap",
                )

        except ImportError:
            # Fallback to platform-specific methods if psutil is not available
            if platform.system() == "Linux":
                self._get_linux_memory_metrics(metrics)
            elif platform.system() == "Darwin":
                self._get_macos_memory_metrics(metrics)
            elif platform.system() == "Windows":
                self._get_windows_memory_metrics(metrics)

        return metrics

    def _get_linux_memory_metrics(self, metrics: Dict[str, PerformanceMetric]) -> None:
        """
        Get memory metrics on Linux.

        Args:
            metrics: Dictionary to update with metrics
        """
        try:
            # Parse /proc/meminfo for memory info
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()

            if self._memory_type == MemoryType.RAM:
                # Get total memory
                mem_total_match = re.search(r"MemTotal:\s+(\d+) kB", meminfo)
                if mem_total_match:
                    total = int(mem_total_match.group(1)) * 1024  # Convert kB to bytes
                    metrics["total"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(total),
                        unit="bytes (total)",
                        device_id="system",
                    )

                # Get available memory
                mem_avail_match = re.search(r"MemAvailable:\s+(\d+) kB", meminfo)
                if mem_avail_match:
                    available = (
                        int(mem_avail_match.group(1)) * 1024
                    )  # Convert kB to bytes
                    metrics["available"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(available),
                        unit="bytes (available)",
                        device_id="system",
                    )

                    # Calculate used memory and utilization
                    if "total" in metrics:
                        total = metrics["total"].value
                        used = total - available

                        metrics["used"] = PerformanceMetric(
                            metric_type=MetricType.MEMORY_USAGE,
                            value=float(used),
                            unit="bytes (used)",
                            device_id="system",
                        )

                        metrics["utilization"] = PerformanceMetric(
                            metric_type=MetricType.UTILIZATION,
                            value=(used / total) * 100 if total > 0 else 0,
                            unit="%",
                            device_id="system",
                        )

            elif self._memory_type == MemoryType.SWAP:
                # Get swap info
                swap_total_match = re.search(r"SwapTotal:\s+(\d+) kB", meminfo)
                swap_free_match = re.search(r"SwapFree:\s+(\d+) kB", meminfo)

                if swap_total_match:
                    total = int(swap_total_match.group(1)) * 1024  # Convert kB to bytes
                    metrics["total"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(total),
                        unit="bytes (total)",
                        device_id="swap",
                    )

                if swap_free_match:
                    free = int(swap_free_match.group(1)) * 1024  # Convert kB to bytes
                    metrics["free"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(free),
                        unit="bytes (free)",
                        device_id="swap",
                    )

                    # Calculate used memory and utilization
                    if "total" in metrics:
                        total = metrics["total"].value
                        used = total - free

                        metrics["used"] = PerformanceMetric(
                            metric_type=MetricType.MEMORY_USAGE,
                            value=float(used),
                            unit="bytes (used)",
                            device_id="swap",
                        )

                        metrics["utilization"] = PerformanceMetric(
                            metric_type=MetricType.UTILIZATION,
                            value=(used / total) * 100 if total > 0 else 0,
                            unit="%",
                            device_id="swap",
                        )

        except Exception as e:
            logger.warning("Error getting Linux memory metrics: %s", str(e))

    def _get_macos_memory_metrics(self, metrics: Dict[str, PerformanceMetric]) -> None:
        """
        Get memory metrics on macOS.

        Args:
            metrics: Dictionary to update with metrics
        """
        try:
            if self._memory_type == MemoryType.RAM:
                # Get total memory
                mem_str = subprocess.check_output(
                    ["sysctl", "-n", "hw.memsize"], text=True
                ).strip()
                if mem_str.isdigit():
                    total = int(mem_str)
                    metrics["total"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(total),
                        unit="bytes (total)",
                        device_id="system",
                    )

                # Get memory usage using vm_stat
                vm_stat = subprocess.check_output(["vm_stat"], text=True)

                # Parse vm_stat output
                page_size_match = re.search(r"page size of (\d+) bytes", vm_stat)
                pages_free_match = re.search(r"Pages free:\s+(\d+)", vm_stat)
                pages_inactive_match = re.search(r"Pages inactive:\s+(\d+)", vm_stat)
                pages_active_match = re.search(r"Pages active:\s+(\d+)", vm_stat)
                pages_wired_match = re.search(r"Pages wired down:\s+(\d+)", vm_stat)

                if (
                    page_size_match
                    and pages_free_match
                    and pages_active_match
                    and pages_wired_match
                ):
                    page_size = int(page_size_match.group(1))
                    pages_free = int(pages_free_match.group(1))
                    pages_inactive = (
                        int(pages_inactive_match.group(1))
                        if pages_inactive_match
                        else 0
                    )
                    pages_active = int(pages_active_match.group(1))
                    pages_wired = int(pages_wired_match.group(1))

                    # Calculate memory metrics
                    available = (pages_free + pages_inactive) * page_size
                    used = (pages_active + pages_wired) * page_size

                    metrics["available"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(available),
                        unit="bytes (available)",
                        device_id="system",
                    )

                    metrics["used"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(used),
                        unit="bytes (used)",
                        device_id="system",
                    )

                    # Calculate utilization
                    if "total" in metrics:
                        total = metrics["total"].value
                        metrics["utilization"] = PerformanceMetric(
                            metric_type=MetricType.UTILIZATION,
                            value=(used / total) * 100 if total > 0 else 0,
                            unit="%",
                            device_id="system",
                        )

            elif self._memory_type == MemoryType.SWAP:
                # Get swap usage
                swap_info = subprocess.check_output(
                    ["sysctl", "-n", "vm.swapusage"], text=True
                )

                # Parse swap info
                total_match = re.search(r"total = (\d+\.\d+)([MGT])B", swap_info)
                used_match = re.search(r"used = (\d+\.\d+)([MGT])B", swap_info)
                free_match = re.search(r"free = (\d+\.\d+)([MGT])B", swap_info)

                if total_match:
                    value = float(total_match.group(1))
                    unit = total_match.group(2)

                    multiplier = {
                        "M": 1024 * 1024,
                        "G": 1024 * 1024 * 1024,
                        "T": 1024 * 1024 * 1024 * 1024,
                    }.get(unit, 1)

                    total = int(value * multiplier)
                    metrics["total"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(total),
                        unit="bytes (total)",
                        device_id="swap",
                    )

                if used_match:
                    value = float(used_match.group(1))
                    unit = used_match.group(2)

                    multiplier = {
                        "M": 1024 * 1024,
                        "G": 1024 * 1024 * 1024,
                        "T": 1024 * 1024 * 1024 * 1024,
                    }.get(unit, 1)

                    used = int(value * multiplier)
                    metrics["used"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(used),
                        unit="bytes (used)",
                        device_id="swap",
                    )

                if free_match:
                    value = float(free_match.group(1))
                    unit = free_match.group(2)

                    multiplier = {
                        "M": 1024 * 1024,
                        "G": 1024 * 1024 * 1024,
                        "T": 1024 * 1024 * 1024 * 1024,
                    }.get(unit, 1)

                    free = int(value * multiplier)
                    metrics["free"] = PerformanceMetric(
                        metric_type=MetricType.MEMORY_USAGE,
                        value=float(free),
                        unit="bytes (free)",
                        device_id="swap",
                    )
        except Exception as e:
            logger.warning("Error getting macOS memory metrics: %s", str(e))

    def _get_windows_memory_metrics(self) -> None:
        """
        Get Windows memory metrics.
        """
        # TODO: Implement Windows memory metrics
        pass
        pass
