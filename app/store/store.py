"""A Redis-like key-value store with support for multiple data types.

This module provides a Store class that supports multiple data types (strings, lists, etc.)
while maintaining Redis's single-type-per-key semantics.
"""
from typing import Dict, List, Optional

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
        """Initialize a new Store instance."""
        # Initialize type-specific stores
        self.stores: Dict[str, BaseStore] = {
            "string": StringStore(),
            "list": ListStore(),
        }
        # Track the type of each key (string, list, etc.)
        self.key_types: Dict[str, str] = {}

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
            return self.stores[expected_type]

        if not key_type:
            raise KeyError(f"Key {key} not found")

        return self.stores[key_type]

    # ===== String Operations (Backward Compatible) =====
    def set_key(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """
        Set the value of a key. If there is an existing key, overwrite it.

        This is the legacy method for backward compatibility.

        Args:
            key: The key to set
            value: The string value to store
            ttl: Optional time to live in milliseconds

        Raises:
            ValueError: If ttl is negative
        """
        if ttl is not None and ttl < 0:
            raise ValueError(f"ERR invalid expire time set: {str(ttl)}")

        store = self.stores["string"]
        if key in self.key_types and self.key_types[key] != "string":
            # Delete existing key of different type
            self.delete_key(key)

        store.set(key, value, ttl)  # type: ignore
        self.key_types[key] = "string"

    def get_key(self, key: str) -> Optional[str]:
        """
        Get the value of a key.

        This is the legacy method for backward compatibility.

        Args:
            key: The key to get

        Returns:
            The string value or None if not found

        Raises:
            TypeError: If the key exists but is not a string
        """
        try:
            store = self._get_store(key)
            if store.get_type() == "string":
                return store.get(key)  # type: ignore
            raise TypeError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            )
        except KeyError:
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

        store = self.stores["list"]
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
        result = store.delete(key)
        if result:
            del self.key_types[key]
        return result
