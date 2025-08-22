"""List store implementation for Redis-like list operations."""
import asyncio
from collections import deque
from typing import TYPE_CHECKING, Deque, Dict, List, Optional, Union

if TYPE_CHECKING:
    from app.blocking.queue_manager import BlockingQueueManager

from .base import BaseStore


class ListStore(BaseStore):
    """Handles storage of list values."""

    def __init__(self, queue_manager: Optional["BlockingQueueManager"] = None):
        """Initialize a new ListStore.

        Args:
            queue_manager: Optional BlockingQueueManager for handling blocking operations
        """
        self.lists: Dict[str, Deque[str]] = {}
        self.queue_manager = queue_manager

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
            self.lists[key] = deque()

        result = None
        for value in values:
            self.lists[key].append(value)
            result = len(self.lists[key])

            # Notify any waiting clients if we have a queue manager
            if self.queue_manager:
                try:
                    # Try to get the running event loop
                    loop = asyncio.get_running_loop()
                    # If we get here, we're in an async context
                    asyncio.create_task(self.queue_manager.notify_push(key, value))
                except RuntimeError:
                    # No event loop running, skip async notification (test environment)
                    pass

        return result or 0

    def lpush(self, key: str, *values: str) -> int:
        """Prepend values to a list, creating it if it doesn't exist.

        Args:
            key: The list key
            *values: Values to prepend

        Returns:
            int: The new length of the list
        """
        if key not in self.lists:
            self.lists[key] = deque()

        result = None
        for value in values:  # Don't reverse the values when prepending
            self.lists[key].appendleft(value)
            result = len(self.lists[key])

            # Notify any waiting clients if we have a queue manager
            if self.queue_manager:
                try:
                    # Try to get the running event loop
                    loop = asyncio.get_running_loop()
                    # If we get here, we're in an async context
                    asyncio.create_task(self.queue_manager.notify_push(key, value))
                except RuntimeError:
                    # No event loop running, skip async notification (test environment)
                    pass

        return result or 0

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

    def llen(self, key: str) -> int:
        """Returns the length of the list for the given key

        Args:
            key: The list key

        Returns:
            The length of the list for the given key
        """
        return len(self.lists[key]) if key in self.lists else 0

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

        # Convert deque to list for slicing since deques don't support slicing directly
        return list(self.lists[key])[norm_start : norm_end + 1]

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

    def flushdb(self) -> None:
        """Deletes all keys from the list store"""
        self.lists.clear()

    def lpop(self, key: str, count: int = None) -> Union[str, List[str], None]:
        """Removes elements from the front of the list and returns them.

        Args:
            key: The key for the list.
            count: Number of elements to pop. If None, pops a single element.

        Returns:
            - Single element if count is None
            - List of elements if count is provided
            - None if list is empty or doesn't exist
        """
        if key not in self.lists or not self.lists.get(key):
            return None if count is None else []

        if count is not None and count <= 0:
            return []

        given_list = self.lists[key]

        if count is None:
            value = given_list.popleft()
            if not given_list:  # Clean up empty lists
                del self.lists[key]
            return value

        count = min(count, len(given_list))
        result = [given_list.popleft() for _ in range(count)]

        if not given_list:  # Clean up empty lists
            del self.lists[key]

        return result
