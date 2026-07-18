"""
Actuation Interface Module

This module provides an interface for modalities to interact with the environment
through different actuation mechanisms. It allows modalities to trigger actions
in the physical or virtual world based on intent processing results.
"""

import logging
import threading
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

# Logger for the module
logger = logging.getLogger(__name__)


class ActuationType(Enum):
    """Enumeration of supported actuation types"""

    # System interactions
    SYSTEM_COMMAND = auto()  # Execute system commands
    NAVIGATE = auto()  # Web/UI navigation

    # UI interactions
    DISPLAY = auto()  # Show content on screen
    NOTIFICATION = auto()  # System notifications

    # Media control
    MEDIA_PLAYBACK = auto()  # Control media playback
    VOLUME = auto()  # Control volume

    # Physical actuation (if hardware available)
    MOTOR = auto()  # Control motors/servos
    LED = auto()  # Control LEDs
    SPEAKER = auto()  # Audio output

    # Virtual assistants
    VOICE_RESPONSE = auto()  # Spoken responses


class ActuationPriority(Enum):
    """Priority levels for actuation requests"""

    CRITICAL = 100  # Safety-critical, interrupt everything
    HIGH = 75  # User-initiated, high priority
    NORMAL = 50  # Standard operations
    LOW = 25  # Background tasks
    DEFER = 10  # Can be delayed if system is busy


class ActuationStatus(Enum):
    """Status of an actuation request"""

    PENDING = auto()  # Waiting to be processed
    EXECUTING = auto()  # Currently executing
    COMPLETED = auto()  # Successfully completed
    FAILED = auto()  # Failed to execute
    CANCELLED = auto()  # Cancelled before execution


class ActuationRequest:
    """
    Represents a request for system actuation.

    This class encapsulates all the information needed to perform
    an actuation in the system.
    """

    def __init__(
        self,
        actuation_type: ActuationType,
        parameters: Dict[str, Any],
        priority: ActuationPriority = ActuationPriority.NORMAL,
        source_modality: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        """
        Initialize an actuation request.

        Args:
            actuation_type: The type of actuation to perform
            parameters: Dictionary of parameters for the actuation
            priority: Priority level for this request
            source_modality: Identifier for the modality creating this request
            request_id: Optional unique identifier for this request
        """
        import uuid

        self.actuation_type = actuation_type
        self.parameters = parameters
        self.priority = priority
        self.source_modality = source_modality
        self.request_id = request_id or str(uuid.uuid4())
        self.status = ActuationStatus.PENDING
        self.created_time = None
        self.execution_time = None
        self.completion_time = None
        self.result = None
        self.error = None

    def __str__(self) -> str:
        """String representation of the actuation request"""
        return (
            f"ActuationRequest(type={self.actuation_type.name}, "
            f"id={self.request_id}, status={self.status.name})"
        )


class ActuationProvider(ABC):
    """
    Abstract base class for actuation providers.

    Each concrete implementation handles a specific type of actuation
    and knows how to execute requests of that type.
    """

    @property
    @abstractmethod
    def supported_actuation_types(self) -> Set[ActuationType]:
        """Return the set of actuation types supported by this provider"""
        pass

    @abstractmethod
    def can_handle(self, request: ActuationRequest) -> bool:
        """
        Check if this provider can handle the given request.

        Args:
            request: The actuation request to check

        Returns:
            True if this provider can handle the request
        """
        pass

    @abstractmethod
    def execute(self, request: ActuationRequest) -> Any:
        """
        Execute the given actuation request.

        Args:
            request: The actuation request to execute

        Returns:
            The result of the actuation, if any

        Raises:
            ActuationError: If the actuation fails
        """
        pass


class ActuationError(Exception):
    """Exception raised when an actuation request fails"""

    pass


class UnsupportedActuationError(ActuationError):
    """Exception raised when no provider supports the requested actuation type"""

    pass


class ActuationManager:
    """
    Manages actuation requests and routes them to appropriate providers.

    This class serves as the central hub for all actuation in the system,
    coordinating between modalities that request actions and the providers
    that can execute those actions.
    """

    def __init__(self):
        """Initialize the actuation manager"""
        self._providers: List[ActuationProvider] = []
        self._request_queue: List[ActuationRequest] = []
        self._lock = threading.RLock()
        self._history: Dict[str, ActuationRequest] = {}
        self._max_history = 100

    def register_provider(self, provider: ActuationProvider) -> None:
        """
        Register a new actuation provider.

        Args:
            provider: The actuation provider to register
        """
        with self._lock:
            self._providers.append(provider)
            logger.debug(
                f"Registered actuation provider supporting: "
                f"{[t.name for t in provider.supported_actuation_types]}"
            )

    def submit(self, request: ActuationRequest, wait: bool = False) -> Optional[Any]:
        """
        Submit an actuation request for execution.

        Args:
            request: The actuation request to submit
            wait: If True, wait for the request to complete and return the result

        Returns:
            If wait is True, the result of the actuation; otherwise None

        Raises:
            UnsupportedActuationError: If no provider supports this actuation type
            ActuationError: If the actuation fails and wait is True
        """
        with self._lock:
            # Find a provider that can handle this request
            provider = self._find_provider(request)
            if not provider:
                error_msg = (
                    f"No provider available for actuation type: "
                    f"{request.actuation_type.name}"
                )
                logger.error(error_msg)
                raise UnsupportedActuationError(error_msg)

            # Add to the queue and history
            self._request_queue.append(request)
            self._history[request.request_id] = request

            # Trim history if needed
            if len(self._history) > self._max_history:
                oldest = min(self._history.values(), key=lambda r: r.created_time or 0)
                if oldest.request_id in self._history:
                    del self._history[oldest.request_id]

        # If not waiting, process asynchronously
        if not wait:
            # In a real implementation, this would use a thread pool
            # For now, just process immediately
            self._process_request(request, provider)
            return None

        # If waiting, process synchronously and return the result
        try:
            result = self._process_request(request, provider)
            return result
        except Exception as e:
            # Re-raise with actuation error
            raise ActuationError(f"Actuation failed: {str(e)}") from e

    def get_request_status(self, request_id: str) -> Optional[ActuationStatus]:
        """
        Get the status of a previously submitted request.

        Args:
            request_id: The unique identifier for the request

        Returns:
            The current status of the request, or None if not found
        """
        with self._lock:
            request = self._history.get(request_id)
            return request.status if request else None

    def get_request_result(self, request_id: str) -> Optional[Any]:
        """
        Get the result of a completed request.

        Args:
            request_id: The unique identifier for the request

        Returns:
            The result of the request, or None if not completed or not found
        """
        with self._lock:
            request = self._history.get(request_id)
            if not request or request.status != ActuationStatus.COMPLETED:
                return None
            return request.result

    def _find_provider(self, request: ActuationRequest) -> Optional[ActuationProvider]:
        """Find a provider that can handle the given request"""
        for provider in self._providers:
            if provider.can_handle(request):
                return provider
        return None

    def _process_request(
        self, request: ActuationRequest, provider: ActuationProvider
    ) -> Any:
        """Process a single actuation request"""
        import time

        try:
            # Update request status
            request.status = ActuationStatus.EXECUTING
            request.execution_time = time.time()

            # Execute the request
            logger.debug(
                f"Executing {request.actuation_type.name} "
                f"actuation (id: {request.request_id})"
            )
            result = provider.execute(request)

            # Update request status
            request.status = ActuationStatus.COMPLETED
            request.completion_time = time.time()
            request.result = result

            return result

        except Exception as e:
            # Update request status
            request.status = ActuationStatus.FAILED
            request.completion_time = time.time()
            request.error = str(e)

            logger.error(
                f"Actuation {request.request_id} failed: {str(e)}", exc_info=True
            )
            raise


# Singleton instance for global access
_actuation_manager_instance = None
_instance_lock = threading.Lock()


def get_actuation_manager() -> ActuationManager:
    """
    Get or create the singleton instance of the ActuationManager.

    Returns:
        The global ActuationManager instance
    """
    global _actuation_manager_instance

    if _actuation_manager_instance is None:
        with _instance_lock:
            if _actuation_manager_instance is None:
                _actuation_manager_instance = ActuationManager()

    return _actuation_manager_instance
