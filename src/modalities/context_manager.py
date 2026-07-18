"""
Context Manager Module

This module provides a context management system for maintaining state across
modality interactions. It implements a persistent memory that can be shared
between different modalities and accessed during intent parsing and processing.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Set

# Logger for the module
logger = logging.getLogger(__name__)


class ContextLevel(Enum):
    """Enumeration of context priority levels for stored information"""

    # Critical information persists indefinitely until explicitly removed
    CRITICAL = 100

    # High priority information with long-term retention
    HIGH = 75

    # Medium priority with moderate retention
    MEDIUM = 50

    # Low priority information that decays quickly
    LOW = 25

    # Temporary information with minimal retention
    TRANSIENT = 10


@dataclass
class ContextItem:
    """
    Represents a single piece of context information stored in memory.

    Attributes:
        key: Unique identifier for this context item
        value: The stored information
        level: Priority/importance level of this context
        timestamp: When this item was created or last updated
        source_modality: Which modality created this context item
        ttl: Time-to-live in seconds (None means no automatic expiration)
        tags: Set of tags for categorizing and searching context items
    """

    key: str
    value: Any
    level: ContextLevel
    timestamp: float = field(default_factory=time.time)
    source_modality: Optional[str] = None
    ttl: Optional[float] = None
    tags: Set[str] = field(default_factory=set)

    def is_expired(self) -> bool:
        """Check if this context item has expired based on its TTL"""
        if self.ttl is None:
            return False
        return (time.time() - self.timestamp) > self.ttl


class ContextManager:
    """
    Manages contextual information and memory shared across modalities.

    This class provides a persistent store of information that can be
    accessed and updated by different modalities. It supports priority
    levels, time-based decay, and tagging for organization.
    """

    def __init__(self) -> None:
        """Initialize the context manager with an empty context store."""
        self._context_store: Dict[str, ContextItem] = {}
        self._lock = threading.RLock()  # Reentrant lock for thread safety

    def set(
        self,
        key: str,
        value: Any,
        level: ContextLevel = ContextLevel.MEDIUM,
        source_modality: Optional[str] = None,
        ttl: Optional[float] = None,
        tags: Optional[Set[str]] = None,
    ) -> None:
        """
        Store or update a piece of context information.

        Args:
            key: Unique identifier for this context item
            value: The information to store
            level: Priority/importance level for this context
            source_modality: Identifier for the modality creating this context
            ttl: Time-to-live in seconds (None means no expiration)
            tags: Optional set of tags for categorizing this context item
        """
        with self._lock:
            self._context_store[key] = ContextItem(
                key=key,
                value=value,
                level=level,
                timestamp=time.time(),
                source_modality=source_modality,
                ttl=ttl,
                tags=tags or set(),
            )
            logger.debug(
                f"Context set: {key} (level: {level.name}, "
                f"source: {source_modality})"
            )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a piece of context information by key.

        Args:
            key: The identifier for the context item to retrieve
            default: Value to return if key is not found or expired

        Returns:
            The stored value, or default if not found or expired
        """
        with self._lock:
            self._cleanup_expired()
            item = self._context_store.get(key)
            if item is None:
                return default

            # Update timestamp to indicate this context is still relevant
            item.timestamp = time.time()
            logger.debug(f"Context accessed: {key}")
            return item.value

    def remove(self, key: str) -> bool:
        """
        Remove a specific context item from the store.

        Args:
            key: The identifier for the context item to remove

        Returns:
            True if the item was found and removed, False otherwise
        """
        with self._lock:
            if key in self._context_store:
                del self._context_store[key]
                logger.debug(f"Context removed: {key}")
                return True
            return False

    def get_by_tags(self, tags: Set[str], require_all: bool = False) -> Dict[str, Any]:
        """
        Retrieve all context items that match the specified tags.

        Args:
            tags: Set of tags to match against context items
            require_all: If True, items must have all specified tags to match
                         If False, items with any of the specified tags match

        Returns:
            Dict mapping keys to values for all matching context items
        """
        with self._lock:
            self._cleanup_expired()
            result = {}

            for key, item in self._context_store.items():
                if require_all:
                    # All specified tags must be present
                    if tags.issubset(item.tags):
                        result[key] = item.value
                else:
                    # Any matching tag is sufficient
                    if tags.intersection(item.tags):
                        result[key] = item.value

            return result

    def get_by_modality(self, modality: str) -> Dict[str, Any]:
        """
        Retrieve all context items created by a specific modality.

        Args:
            modality: The source modality identifier to filter by

        Returns:
            Dict mapping keys to values for all matching context items
        """
        with self._lock:
            self._cleanup_expired()
            return {
                key: item.value
                for key, item in self._context_store.items()
                if item.source_modality == modality
            }

    def get_all_context(
        self, include_expired: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all context items with their metadata.

        Args:
            include_expired: Whether to include expired items in the result

        Returns:
            Dict mapping keys to dicts containing value and metadata
        """
        with self._lock:
            if not include_expired:
                self._cleanup_expired()

            return {
                key: {
                    "value": item.value,
                    "level": item.level.name,
                    "timestamp": item.timestamp,
                    "age": time.time() - item.timestamp,
                    "source_modality": item.source_modality,
                    "ttl": item.ttl,
                    "tags": list(item.tags),
                    "expired": item.is_expired(),
                }
                for key, item in self._context_store.items()
            }

    def clear(self, min_level: Optional[ContextLevel] = None) -> int:
        """
        Clear context items from the store, optionally preserving items
        above a specified importance level.

        Args:
            min_level: If provided, only remove items below this level

        Returns:
            Number of items removed
        """
        with self._lock:
            count_before = len(self._context_store)

            if min_level is None:
                self._context_store.clear()
                logger.debug("All context cleared")
            else:
                # Remove only items below the specified level
                keys_to_remove = [
                    key
                    for key, item in self._context_store.items()
                    if item.level.value < min_level.value
                ]
                for key in keys_to_remove:
                    del self._context_store[key]

                logger.debug(f"Cleared context below level {min_level.name}")

            return count_before - len(self._context_store)

    def _cleanup_expired(self) -> int:
        """
        Remove expired context items from the store.

        Returns:
            Number of expired items removed
        """
        keys_to_remove = [
            key for key, item in self._context_store.items() if item.is_expired()
        ]

        for key in keys_to_remove:
            del self._context_store[key]

        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} expired context items")

        return len(keys_to_remove)


# Singleton instance for global access
_context_manager_instance = None
_instance_lock = threading.Lock()


def get_context_manager() -> ContextManager:
    """
    Get or create the singleton instance of the ContextManager.

    Returns:
        The global ContextManager instance
    """
    global _context_manager_instance

    if _context_manager_instance is None:
        with _instance_lock:
            if _context_manager_instance is None:
                _context_manager_instance = ContextManager()

    return _context_manager_instance
