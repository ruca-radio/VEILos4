import psutil
import time
import logging
from collections import defaultdict
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SelfMonitorError(Exception):
    """Custom exception for self-monitoring errors."""
    pass

class SelfMonitor:
    """Collects and tracks system and operational metrics for VEILos."""

    def __init__(self):
        self._operational_metrics: Dict[str, Any] = defaultdict(int)
        self._last_cpu_times = psutil.cpu_times()
        self._last_net_io = psutil.net_io_counters()
        logger.info("SelfMonitor initialized.")

    def get_system_metrics(self) -> Dict[str, float]:
        """
        Collects current system resource usage metrics.
        Returns:
            A dictionary of system metrics.
        """
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "network_bytes_sent": psutil.net_io_counters().bytes_sent,
            "network_bytes_recv": psutil.net_io_counters().bytes_recv,
            "process_count": len(psutil.pids())
        }
        return metrics

    def record_operational_metric(self, metric_name: str, value: int = 1):
        """
        Records or increments an operational metric.
        Args:
            metric_name: The name of the operational metric.
            value: The value to add to the metric (default is 1 for increments).
        """
        self._operational_metrics[metric_name] += value
        logger.debug(f"Recorded operational metric '{metric_name}': {self._operational_metrics[metric_name]}")

    def get_operational_metrics(self) -> Dict[str, Any]:
        """
        Returns all recorded operational metrics.
        """
        return dict(self._operational_metrics)

    def reset_operational_metrics(self):
        """
        Resets all operational metrics to zero.
        """
        self._operational_metrics = defaultdict(int)
        logger.info("Operational metrics reset.")

    def get_combined_metrics(self) -> Dict[str, Any]:
        """
        Returns a dictionary containing both system and operational metrics.
        """
        combined = {"timestamp": time.time()}
        combined.update(self.get_system_metrics())
        combined.update(self.get_operational_metrics())
        return combined