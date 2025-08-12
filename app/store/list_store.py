"""List store implementation for Redis-like list operations."""
from typing import Dict, List

from .base import BaseStore


class ListStore(BaseStore):
    """Handles storage of list values."""

    def __init__(self):
        """Initialize a new ListStore."""
        self.lists: Dict[str, List[str]] = {}

    def get_type(self) -> str:
        """Return the type name of this store."""
        return "list"

    def rpush(self, key: str, *values: str) -> int:
        """Append values to a list, creating it if it doesn't exist.

        Args:
            key: The list key
            *values: Values to append

        Returns:
            int: The new length of the list
        """
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].extend(values)
        return len(self.lists[key])

    def lrange(self, key: str, start: int, end: int) -> List[str]:
        """Get a range of elements from a list.

        Args:
            key: The list key
            start: Start index (0-based, negative values count from the end)
            end: End index (inclusive, negative values count from the end)

        Returns:
            List of elements in the specified range
        """
        if key not in self.lists:
            return []

        lst = self.lists[key]
        length = len(lst)
        start = max(start + length, 0) if start < 0 else min(start, length)
        end = max(end + length, 0) if end < 0 else min(end + 1, length)
        return lst[start:end] if start < end else []

    def delete(self, key: str) -> bool:
        """Delete a key from the list store.

        Args:
            key: The key to delete

        Returns:
            bool: True if the key existed and was deleted
        """
        existed = key in self.lists
        self.lists.pop(key, None)
        return existed
