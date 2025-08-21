"""A Redis-like key-value store with support for multiple data types.

This module provides the Store class which is the main interface for all data storage
operations in the Redis server. It manages different data types (strings, lists, etc.)
while maintaining Redis's single-type-per-key semantics.
"""
import time
from typing import Callable, Dict, List, Optional

from app.blocking.queue_manager import BlockingQueueManager

# Import store implementations
from .base import BaseStore
from .list_store import ListStore
from .string_store import StringStore


class Store:
    """Main store class that manages different data types.

    This class provides backward compatibility with the old store interface
    while adding support for multiple data types.
    """

    def __init__(self):
        """Initialize the store with empty dictionaries and a BlockingQueueManager."""
        self.stores: Dict[str, BaseStore] = {}
        self.key_types: Dict[str, str] = {}
        # Default to real time function
        self._time_func = lambda: time.time() * 1000  # ms since epoch
        self._blocking_queue_manager = BlockingQueueManager()

        # Initialize default stores
        self._init_stores()

    def _init_stores(self) -> None:
        """Initialize the default stores with the blocking queue manager."""
        # String store with expiration support
        self.stores["string"] = StringStore(
            on_delete=self._on_key_deleted, time_func=self._time_func
        )

        # List store with blocking operation support
        self.stores["list"] = ListStore(queue_manager=self._blocking_queue_manager)

    def _get_or_create_store(self, key_type: str) -> BaseStore:
        """Get or create a store for the given key type.

        Args:
            key_type: The type of store to get or create

        Returns:
            The store instance
        """
        if key_type not in self.stores:
            if key_type == "string":
                self.stores[key_type] = StringStore(
                    on_delete=self._on_key_deleted, time_func=self._time_func
                )
            elif key_type == "list":
                self.stores[key_type] = ListStore(
                    queue_manager=self._blocking_queue_manager
                )
            else:
                raise ValueError(f"Unsupported key type: {key_type}")
        return self.stores[key_type]

    def _get_store(self, key: str, expected_type: Optional[str] = None) -> BaseStore:
        """Get the store for a key, with optional type checking.

        Args:
            key: The key to get the store for
            expected_type: Optional expected type of the key

        Returns:
            The appropriate store instance

        Raises:
            TypeError: If the key exists with a different type than expected
            KeyError: If the key doesn't exist and no expected_type is provided
        """
        key_type = self.key_types.get(key)

        if expected_type and key_type and key_type != expected_type:
            raise TypeError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )

        if not key_type and expected_type:
            self.key_types[key] = expected_type
            return self._get_or_create_store(expected_type)

        if not key_type:
            raise KeyError(f"Key {key} not found")

        return self.stores[key_type]

    def get_list_store(self) -> "ListStore":
        """Get the list store instance.

        Returns:
            ListStore: The list store instance
        """
        return self._get_or_create_store("list")

    def _on_key_deleted(self, key: str) -> None:
        """Callback when a key is deleted from a store.

        Args:
            key: The key that was deleted
        """
        self.key_types.pop(key, None)

    def set_time_function(self, time_func: Callable[[], float]) -> None:
        """Set a custom time function for testing.

        Args:
            time_func: Function that returns current time in milliseconds since epoch.
        """
        self._time_func = time_func
        # Update the time function in the string store if it exists
        if "string" in self.stores:
            self.stores["string"].set_time_function(time_func)

    # ===== String Operations (Backward Compatible) =====
    def set_key(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """
        Set the value of a key. If there is an existing key, overwrite it.

        Args:
            key: The key to set
            value: The string value to store
            ttl: Optional time to live in milliseconds

        Raises:
            ValueError: If ttl is negative
        """
        if ttl is not None and ttl < 0:
            raise ValueError(f"ERR invalid expire time set: {str(ttl)}")

        store = self._get_or_create_store("string")
        if key in self.key_types and self.key_types[key] != "string":
            # Delete existing key of different type
            self.delete_key(key)

        store.set(key, value, ttl)  # type: ignore
        self.key_types[key] = "string"

    def get_key(self, key: str) -> Optional[str]:
        """
        Get the value of a key.

        Args:
            key: The key to get

        Returns:
            The string value or None if not found

        Raises:
            TypeError: If the key exists but is not a string
        """
        if key not in self.key_types:
            return None

        try:
            store = self.stores[self.key_types[key]]
            if store.get_type() == "string":
                return store.get(key)
            raise TypeError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )
        except KeyError:
            # Key exists in key_types but not in the store (possibly expired)
            del self.key_types[key]
            return None

    # ===== List Operations =====
    def rpush(self, key: str, *values: str) -> int:
        """Append values to a list, creating it if it doesn't exist.

        Args:
            key: The list key
            *values: Values to append

        Returns:
            The new length of the list

        Raises:
            TypeError: If the key exists but is not a list
        """
        if key in self.key_types and self.key_types[key] != "list":
            raise TypeError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )

        store = self._get_or_create_store("list")
        if key not in self.key_types:
            self.key_types[key] = "list"

        return store.rpush(key, *values)  # type: ignore

    def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get a range of elements from a list.

        Args:
            key: The list key
            start: Start index (0-based, negative values count from the end)
            end: End index (inclusive, negative values count from the end)

        Returns:
            List of elements in the specified range

        Raises:
            TypeError: If the key exists but is not a list
        """

        store = self._get_store(key, "list")
        return store.lrange(key, start, end)  # type: ignore

    def lpush(self, key: str, *values: str) -> int:
        """Append values to a list, creating it if it doesn't exist.

        Args:
            key: The list key
            *values: Values to append

        Returns:
            The new length of the list

        Raises:
            TypeError: If the key exists but is not a list
        """
        if key in self.key_types and self.key_types[key] != "list":
            raise TypeError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )

        store = self._get_or_create_store("list")
        if key not in self.key_types:
            self.key_types[key] = "list"

        return store.lpush(key, *values)

    def llen(self, key: str) -> int:
        """Get the length of the list.

        Args:
            key: The list key.

        Returns:
            The length of the list.

        Raises:
            TypeError: If the key exists, but is not a list.
        """
        if key in self.key_types and self.key_types[key] != "list":
            raise TypeError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )

        store = self._get_or_create_store("list")
        if key not in self.key_types:
            self.key_types[key] = "list"

        return store.llen(key)

    def lpop(self, key: str, count: int = None) -> str:
        """Removes the element at the front of the list for the given key.

        Args:
            key: The list key

        Returns:
            The element at the front of the list of the given key.\
                 If list is empty or doesn't exist, return -1.

        Raises:
            TypeError: If the key exists, but is not a list.
        """
        if key in self.key_types and self.key_types[key] != "list":
            raise TypeError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )
        store = self._get_or_create_store("list")
        return store.lpop(key, count)

    # ===== Common Operations =====
    def delete_key(self, key: str) -> bool:
        """Delete a key from the store.

        Args:
            key: The key to delete

        Returns:
            bool: True if the key existed and was deleted, False otherwise
        """
        if key not in self.key_types:
            return False

        store = self.stores[self.key_types[key]]
        return store.delete(key)

    async def shutdown(self) -> None:
        """Clean up resources on server shutdown."""
        await self._blocking_queue_manager.shutdown()

    def flushdb(self) -> bool:
        """Delete all keys from all stores.

        Returns:
            bool: Always returns True
        """
        for store in self.stores.values():
            store.flushdb()
        self.key_types.clear()
        return True
