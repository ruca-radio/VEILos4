"""
Introspection Module

This module provides mechanisms for modalities to examine their own
performance, record metrics, and enable continuous improvement through
self-monitoring and adaptation.
"""

import logging
import threading
import time
from enum import Enum
from typing import Any, Dict, List, Optional

# Logger for the module
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be tracked"""

    # Timing metrics
    LATENCY = "latency"  # Processing time
    THROUGHPUT = "throughput"  # Items processed per time unit

    # Accuracy metrics
    CONFIDENCE = "confidence"  # Confidence score
    ACCURACY = "accuracy"  # Measured accuracy (requires feedback)
    ERROR_RATE = "error_rate"  # Rate of errors

    # Resource usage
    CPU_USAGE = "cpu_usage"  # CPU utilization
    MEMORY_USAGE = "memory_usage"  # Memory utilization

    # User interaction
    USER_SATISFACTION = "user_satisfaction"  # User satisfaction score
    USER_CORRECTION = "user_correction"  # User needed to correct output

    # System
    FALLBACK_RATE = "fallback_rate"  # Rate of fallback usage
    IMPROVEMENT_RATE = "improvement_rate"  # Rate of self-improvement


class PerformanceMetric:
    """
    Represents a performance metric that can be tracked over time.

    This class supports tracking values, computing statistics, and
    analyzing trends for a single performance metric.
    """

    def __init__(
        self,
        metric_type: MetricType,
        modality_type: Optional[str] = None,
        window_size: int = 100,
    ):
        """
        Initialize a new performance metric.

        Args:
            metric_type: The type of metric being tracked
            modality_type: The modality type this metric belongs to
            window_size: Maximum number of values to keep in history
        """
        self.metric_type = metric_type
        self.modality_type = modality_type
        self.window_size = window_size
        self.values: List[float] = []
        self.timestamps: List[float] = []
        self._lock = threading.RLock()

    def add_value(self, value: float) -> None:
        """
        Add a new value to the metric history.

        Args:
            value: The metric value to add
        """
        with self._lock:
            self.values.append(value)
            self.timestamps.append(time.time())

            # Keep history within window size
            if len(self.values) > self.window_size:
                self.values.pop(0)
                self.timestamps.pop(0)

    def get_average(self, window: Optional[int] = None) -> Optional[float]:
        """
        Get the average value over the specified window.

        Args:
            window: Number of most recent values to average (None for all)

        Returns:
            Average value, or None if no values available
        """
        with self._lock:
            if not self.values:
                return None

            if window is not None and window < len(self.values):
                values = self.values[-window:]
            else:
                values = self.values

            return sum(values) / len(values)

    def get_trend(self, window: Optional[int] = None) -> Optional[float]:
        """
        Calculate the trend (rate of change) of this metric.

        Args:
            window: Number of most recent values to consider (None for all)

        Returns:
            Trend value (positive = increasing, negative = decreasing),
            or None if not enough data
        """
        with self._lock:
            if len(self.values) < 2:
                return None

            if window is not None and window < len(self.values):
                values = self.values[-window:]
                timestamps = self.timestamps[-window:]
            else:
                values = self.values
                timestamps = self.timestamps

            if len(values) < 2:
                return None

            # Simple linear regression slope
            n = len(values)
            sum_x = sum(timestamps)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(timestamps, values))
            sum_xx = sum(x * x for x in timestamps)

            # Calculate slope (trend)
            try:
                numerator = n * sum_xy - sum_x * sum_y
                denominator = n * sum_xx - sum_x * sum_x
                slope = numerator / denominator
                return slope
            except ZeroDivisionError:
                return None


class IntrospectionTracker:
    """
    Tracks performance metrics and provides insights for self-improvement.

    This class collects and analyzes performance data from modality operations,
    enabling modalities to monitor their own performance and adapt over time.
    """

    def __init__(self):
        """Initialize the introspection tracker"""
        self._metrics: Dict[str, PerformanceMetric] = {}
        self._lock = threading.RLock()

    def track_metric(
        self,
        metric_type: MetricType,
        value: float,
        modality_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a performance metric value.

        Args:
            metric_type: The type of metric to track
            value: The metric value
            modality_type: The modality type this metric belongs to
            context: Additional contextual information about this metric
        """
        with self._lock:
            # Create unique key for this metric + modality combination
            key = f"{metric_type.value}:{modality_type or 'general'}"

            # Create metric if it doesn't exist
            if key not in self._metrics:
                metric = PerformanceMetric(
                    metric_type=metric_type, modality_type=modality_type
                )
                self._metrics[key] = metric

            # Add the value
            self._metrics[key].add_value(value)

            # Log for debugging
            logger.debug(
                f"Tracked {metric_type.value} = {value} "
                f"for {modality_type or 'general'}"
            )

    def get_metric_average(
        self,
        metric_type: MetricType,
        modality_type: Optional[str] = None,
        window: Optional[int] = None,
    ) -> Optional[float]:
        """
        Get the average value for a specific metric.

        Args:
            metric_type: The type of metric
            modality_type: The modality type
            window: Number of most recent values to consider

        Returns:
            Average value, or None if no data available
        """
        with self._lock:
            key = f"{metric_type.value}:{modality_type or 'general'}"
            metric = self._metrics.get(key)
            if not metric:
                return None
            return metric.get_average(window)

    def get_metric_trend(
        self,
        metric_type: MetricType,
        modality_type: Optional[str] = None,
        window: Optional[int] = None,
    ) -> Optional[float]:
        """
        Get the trend for a specific metric.

        Args:
            metric_type: The type of metric
            modality_type: The modality type
            window: Number of most recent values to consider

        Returns:
            Trend value, or None if insufficient data
        """
        with self._lock:
            key = f"{metric_type.value}:{modality_type or 'general'}"
            metric = self._metrics.get(key)
            if not metric:
                return None
            return metric.get_trend(window)

    def get_all_metrics(
        self, modality_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all metrics for a specific modality or all modalities.

        Args:
            modality_type: Optional modality type to filter by

        Returns:
            Dictionary of metric data
        """
        with self._lock:
            result = {}

            for key, metric in self._metrics.items():
                # Skip if not matching the requested modality
                # Check if modality doesn't match filter
                has_filter = modality_type is not None
                not_matching = metric.modality_type != modality_type
                mod_match = has_filter and not_matching
                if mod_match:
                    continue

                # Add to result
                result[key] = {
                    "type": metric.metric_type.value,
                    "modality": metric.modality_type,
                    "average": metric.get_average(),
                    "trend": metric.get_trend(),
                    "count": len(metric.values),
                    "latest": metric.values[-1] if metric.values else None,
                }

            return result

    def get_improvement_opportunities(
        self, modality_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze metrics to identify opportunities for improvement.

        This method looks for metrics with negative trends or below-threshold
        values that suggest areas where the modality could improve.

        Args:
            modality_type: Optional modality type to filter by

        Returns:
            List of improvement opportunities with metrics and suggestions
        """
        # Thresholds for various metrics (would be configurable in real system)
        thresholds = {
            MetricType.CONFIDENCE: 0.7,  # Min acceptable confidence
            MetricType.ACCURACY: 0.8,  # Min acceptable accuracy
            MetricType.ERROR_RATE: 0.2,  # Max acceptable error rate
            MetricType.FALLBACK_RATE: 0.1,  # Max acceptable fallback rate
        }

        opportunities = []

        with self._lock:
            for key, metric in self._metrics.items():
                # Skip if not matching the requested modality
                # Check if modality doesn't match filter
                has_filter = modality_type is not None
                not_matching = metric.modality_type != modality_type
                if has_filter and not_matching:
                    continue

                avg = metric.get_average()
                trend = metric.get_trend()

                if avg is None or trend is None:
                    continue

                # Check against thresholds
                suggestion = None
                if metric.metric_type in thresholds:
                    threshold = thresholds[metric.metric_type]

                    # For metrics where higher is better
                    if metric.metric_type in [
                        MetricType.CONFIDENCE,
                        MetricType.ACCURACY,
                    ]:
                        if avg < threshold:
                            suggestion = (
                                f"Improve {metric.metric_type.value} "
                                f"(current: {avg:.2f}, "
                                f"target: {threshold:.2f})"
                            )

                    # For metrics where lower is better
                    elif metric.metric_type in [
                        MetricType.ERROR_RATE,
                        MetricType.FALLBACK_RATE,
                    ]:
                        if avg > threshold:
                            suggestion = (
                                f"Reduce {metric.metric_type.value} "
                                f"(current: {avg:.2f}, "
                                f"target: {threshold:.2f})"
                            )

                # Check trends
                trend_suggestion = None
                high_quality_metrics = [
                    MetricType.CONFIDENCE,
                    MetricType.ACCURACY,
                ]
                if metric.metric_type in high_quality_metrics:
                    if trend < 0:
                        trend_suggestion = (
                            f"{metric.metric_type.value} is declining, "
                            f"investigate causes"
                        )
                elif metric.metric_type in [
                    MetricType.ERROR_RATE,
                    MetricType.FALLBACK_RATE,
                    MetricType.LATENCY,
                ]:
                    if trend > 0:
                        trend_suggestion = (
                            f"{metric.metric_type.value} is increasing, "
                            f"investigate causes"
                        )

                # Add to opportunities if there's something to improve
                if suggestion or trend_suggestion:
                    opportunities.append(
                        {
                            "metric": metric.metric_type.value,
                            "modality": metric.modality_type,
                            "current_value": avg,
                            "trend": trend,
                            "suggestion": suggestion or trend_suggestion,
                        }
                    )

        return opportunities


# Singleton instance for global access
_introspection_tracker_instance = None
_instance_lock = threading.Lock()


def get_introspection_tracker() -> IntrospectionTracker:
    """
    Get or create the singleton instance of the IntrospectionTracker.

    Returns:
        The global IntrospectionTracker instance
    """
    global _introspection_tracker_instance

    if _introspection_tracker_instance is None:
        with _instance_lock:
            if _introspection_tracker_instance is None:
                _introspection_tracker_instance = IntrospectionTracker()

    return _introspection_tracker_instance
