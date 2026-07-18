"""
Base Storage Interface

This module defines the base interfaces for persistent storage providers
used by the enhanced context manager.
"""

import abc
import json
import logging
import pickle
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TypeAlias

# Type aliases for complex types
QueryResult: TypeAlias = List[Tuple[str, Any, Dict[str, Any]]]

# Logger for the module
logger = logging.getLogger(__name__)


class SerializationType(Enum):
    """Enumeration of serialization types for stored objects"""

    JSON = "json"
    PICKLE = "pickle"
    STRING = "string"


class StorageError(Exception):
    """Base exception for storage-related errors"""

    pass


class StorageConnectionError(StorageError):
    """Exception raised when unable to connect to storage backend"""

    pass


class StorageReadError(StorageError):
    """Exception raised when reading from storage fails"""

    pass


class StorageWriteError(StorageError):
    """Exception raised when writing to storage fails"""

    pass


class Serializer:
    """
    Utility class for serializing and deserializing objects for storage.

    This class handles conversion between Python objects and serialized formats
    that can be stored in various storage backends.
    """

    @staticmethod
    def serialize(
        obj: Any,
        serialization_type: SerializationType = SerializationType.JSON,
    ) -> Tuple[bytes, SerializationType]:
        """
        Serialize an object to bytes using the specified serialization type.

        Args:
            obj: The object to serialize
            serialization_type: The serialization method to use

        Returns:
            Tuple of (serialized_bytes, actual_serialization_type)

        Raises:
            ValueError: If serialization fails
        """
        try:
            if serialization_type == SerializationType.JSON:
                # For JSON serialization, we need to handle special types
                # like sets, datetimes, etc.
                if isinstance(obj, set):
                    obj = {"__type": "set", "items": list(obj)}
                elif isinstance(obj, datetime):
                    obj = {"__type": "datetime", "timestamp": obj.timestamp()}

                # Handle types not supported by JSON
                serialized = json.dumps(obj).encode("utf-8")
                return serialized, SerializationType.JSON

            elif serialization_type == SerializationType.PICKLE:
                serialized = pickle.dumps(obj)
                return serialized, SerializationType.PICKLE

            elif serialization_type == SerializationType.STRING:
                if isinstance(obj, str):
                    serialized = obj.encode("utf-8")
                else:
                    serialized = str(obj).encode("utf-8")
                return serialized, SerializationType.STRING

            else:
                raise ValueError(
                    f"Unsupported serialization type: {serialization_type}"
                )

        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            # Fall back to pickle if JSON fails
            if serialization_type == SerializationType.JSON:
                logger.warning("Falling back to pickle serialization")
                return Serializer.serialize(obj, SerializationType.PICKLE)
            raise ValueError(f"Failed to serialize object: {str(e)}")

    @staticmethod
    def deserialize(data: bytes, serialization_type: SerializationType) -> Any:
        """
        Deserialize bytes back to a Python object.

        Args:
            data: The serialized data
            serialization_type: The serialization method used

        Returns:
            The deserialized object

        Raises:
            ValueError: If deserialization fails
        """
        try:
            if serialization_type == SerializationType.JSON:
                obj = json.loads(data.decode("utf-8"))

                # Handle special types that were serialized
                if isinstance(obj, dict) and "__type" in obj:
                    if obj["__type"] == "set":
                        return set(obj["items"])
                    elif obj["__type"] == "datetime":
                        return datetime.fromtimestamp(obj["timestamp"])
                return obj

            elif serialization_type == SerializationType.PICKLE:
                return pickle.loads(data)

            elif serialization_type == SerializationType.STRING:
                return data.decode("utf-8")

            else:
                raise ValueError(
                    f"Unsupported serialization type: {serialization_type}"
                )

        except Exception as e:
            logger.error(f"Deserialization error: {str(e)}")
            raise ValueError(f"Failed to deserialize object: {str(e)}")


class StorageProvider(abc.ABC):
    """
    Abstract base class for storage providers.

    Each concrete implementation handles the storage and retrieval of
    context items in a specific backend (SQLite, Redis, etc.).
    """

    @abc.abstractmethod
    def initialize(self) -> None:
        """
        Initialize the storage provider.

        This method should establish any necessary connections, create
        tables/collections, and prepare the storage for use.

        Raises:
            StorageConnectionError: If initialization fails
        """
        pass

    @abc.abstractmethod
    def store(
        self,
        key: str,
        value: Any,
        metadata: Dict[str, Any],
        serialization_type: Optional[SerializationType] = None,
    ) -> None:
        """
        Store a value with its metadata.

        Args:
            key: The unique key for the stored item
            value: The value to store
            metadata: Additional metadata about the stored item
            serialization_type: Optional preferred serialization method

        Raises:
            StorageWriteError: If storing fails
        """
        pass

    @abc.abstractmethod
    def retrieve(self, key: str) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Retrieve a value and its metadata by key.

        Args:
            key: The key of the item to retrieve

        Returns:
            Tuple of (value, metadata) if found, None otherwise

        Raises:
            StorageReadError: If retrieval fails
        """
        pass

    @abc.abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete an item by key.

        Args:
            key: The key of the item to delete

        Returns:
            True if the item was found and deleted, False otherwise

        Raises:
            StorageWriteError: If deletion fails
        """
        pass

    @abc.abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """
        List all keys in the storage, optionally filtered by prefix.

        Args:
            prefix: Optional prefix to filter keys

        Returns:
            List of keys

        Raises:
            StorageReadError: If listing fails
        """
        pass

    @abc.abstractmethod
    def query(self, filters: Dict[str, Any]) -> QueryResult:
        """
        Query items based on metadata filters.

        Args:
            filters: Dictionary of metadata key-value pairs to match

        Returns:
            List of (key, value, metadata) tuples for matching items

        Raises:
            StorageReadError: If querying fails
        """
        pass

    @abc.abstractmethod
    def clear(self) -> int:
        """
        Clear all items from the storage.

        Returns:
            Number of items removed

        Raises:
            StorageWriteError: If clearing fails
        """
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """
        Close the storage provider, releasing any resources.

        Raises:
            StorageError: If closing fails
        """
        pass
