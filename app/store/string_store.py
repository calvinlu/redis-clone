"""String store implementation for Redis-like string operations."""
import time
from typing import Any, Callable, Dict, Optional

from .base import BaseStore


class StringStore(BaseStore):
    """Handles storage of string values with expiration."""

    def __init__(
        self,
        on_delete: Optional[Callable[[str], None]] = None,
        time_func: Optional[Callable[[], float]] = None,
    ):
        """Initialize a new StringStore.

        Args:
            on_delete: Optional callback function that will be called with the key
                     when a key is deleted due to expiration or explicit deletion.
            time_func: Optional function that returns current time in seconds since epoch.
                     Defaults to time.time(). Will be multiplied by 1000 for ms precision.
        """
        self.values: Dict[str, str] = {}
        self.expirations: Dict[str, float] = {}
        self._on_delete = on_delete
        self._time_func = time_func or (lambda: time.time() * 1000)

    def get_type(self) -> str:
        """Return the type name of this store."""
        return "string"

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a string value with optional TTL in milliseconds.

        Args:
            key: The key to set
            value: The value to store (will be converted to string)
            ttl: Optional time to live in milliseconds
        """
        self.values[key] = str(value) if value is not None else ""
        if ttl is not None:
            self.expirations[key] = self._time_func() + ttl
        elif key in self.expirations:
            del self.expirations[key]

    def get(self, key: str) -> Optional[str]:
        """Get a string value, checking for expiration.

        Args:
            key: The key to get

        Returns:
            The string value or None if not found/expired
        """
        if key not in self.values:
            return None

        current_time = self._time_func()
        if key in self.expirations and current_time > self.expirations[key]:
            self.delete(key)
            return None

        return self.values[key]

    def delete(self, key: str) -> bool:
        """Delete a key from the string store.

        Args:
            key: The key to delete

        Returns:
            bool: True if the key was deleted, False if it didn't exist
        """
        existed = key in self.values
        if existed:
            self.values.pop(key, None)
            self.expirations.pop(key, None)
            if self._on_delete:
                self._on_delete(key)
        return existed

    def flushdb(self) -> None:
        """Delete all entries from the string store."""
        if self._on_delete:
            for key in list(self.values.keys()):
                self._on_delete(key)
        self.values.clear()
        self.expirations.clear()

    def ttl(self, key: str) -> Optional[int]:
        """Get the remaining time to live of a key in milliseconds.

        Args:
            key: The key to check

        Returns:
            TTL in milliseconds if the key exists and has a TTL,
            -1 if the key exists but has no TTL,
            None if the key doesn't exist
        """
        if key not in self.values:
            return None

        if key not in self.expirations:
            return -1

        remaining = self.expirations[key] - self._time_func()
        return max(0, int(remaining)) if remaining > 0 else -2
