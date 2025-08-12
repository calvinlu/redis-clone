"""A simple key-value store implementation.

This module provides a basic key-value store with get and set operations.
"""
import time
from typing import Optional


class Store:
    """A simple key-value store class.

    This class provides basic key-value storage functionality with get and set operations.
    """

    def __init__(self):
        """Initialize a new Store instance with an empty dictionary."""
        self.store = {}
        self.expirations = {}

    def get_key(self, key: str) -> str:
        """
        Get the value of a key.

        Args:
            key: The key to get

        Returns:
            The value of the key. Returns None if key does not exist.
        """
        if key not in self.store:
            return None

        expiration_time = self.expirations.get(key)
        current_time = time.time() * 1000

        if expiration_time is not None and current_time > expiration_time:
            del self.store[key]
            del self.expirations[key]
            return None

        return self.store.get(key)

    def set_key(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """
        Set the value of a key. If there is an existing key, overwrite it.

        Args:
            key: The key to set.
            value: The value of the key to set.
            Optional[ttl]: The time to live for the given key in milliseconds.

        Returns:
            None

        Raises:
            ValueError: If ttl is negative.
        """
        if ttl is not None and ttl < 0:
            raise ValueError(f"ERR invalid expire time set: {str(ttl)}")
        if ttl is not None:
            self.expirations[key] = (time.time() * 1000) + ttl
        self.store[key] = str(value) if value is not None else ""
