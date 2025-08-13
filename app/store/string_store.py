"""String store implementation for Redis-like string operations."""
import time
from typing import Dict, Optional

from .base import BaseStore


class StringStore(BaseStore):
    """Handles storage of string values with expiration."""

    def __init__(self):
        """Initialize a new StringStore."""
        self.values: Dict[str, str] = {}
        self.expirations: Dict[str, float] = {}

    def get_type(self) -> str:
        """Return the type name of this store."""
        return "string"

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set a string value with optional TTL in milliseconds.

        Args:
            key: The key to set
            value: The string value
            ttl: Optional time to live in milliseconds
        """
        self.values[key] = str(value) if value is not None else ""
        if ttl is not None:
            self.expirations[key] = time.time() * 1000 + ttl
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

        if key in self.expirations and time.time() * 1000 > self.expirations[key]:
            self.delete(key)
            return None

        return self.values[key]

    def delete(self, key: str) -> bool:
        """Delete a key from the string store.

        Args:
            key: The key to delete

        Returns:
            bool: True if the key existed and was deleted
        """
        existed = key in self.values
        self.values.pop(key, None)
        self.expirations.pop(key, None)
        return existed

    def flushdb(self) -> None:
        """Deletes all entries from the string store."""
        self.values.clear()
        self.expirations.clear()
