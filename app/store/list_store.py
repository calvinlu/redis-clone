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

    def _normalize_start_index(self, index: int, length: int) -> int:
        """Normalize the start index according to Redis LRANGE behavior.

        Args:
            index: The start index (can be negative)
            length: The length of the list

        Returns:
            The normalized start index (0-based, non-negative)
        """
        if index < 0:
            return max(index + length, 0)
        return min(index, length)  # For start, we can go up to length (exclusive)

    def _normalize_end_index(self, index: int, length: int) -> int:
        """Normalize the end index according to Redis LRANGE behavior.

        Args:
            index: The end index (can be negative, inclusive)
            length: The length of the list

        Returns:
            The normalized end index (0-based, can be -1 for empty ranges)
        """
        if index < 0:
            return max(index + length, -1)  # Can be -1 for empty ranges
        return min(index, length - 1)  # For end, we cap at length-1

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

        # Normalize indices
        norm_start = self._normalize_start_index(start, length)
        norm_end = self._normalize_end_index(end, length)

        # Check if range is valid
        if norm_start > norm_end or norm_start >= length:
            return []

        # Return the slice (end + 1 because Python slicing is exclusive)
        return lst[norm_start : norm_end + 1]

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
