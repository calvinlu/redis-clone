"""Manages blocking operations for Redis list commands.

This module provides a centralized way to handle blocking operations for list commands
like BLPOP, BRPOP, etc. It maintains a registry of clients waiting for data on specific
keys and notifies them when data becomes available.
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class BlockingOperation:
    """Represents a single blocking operation waiting for data."""

    event: asyncio.Event
    key: str
    timeout: float
    future: asyncio.Future[Tuple[Optional[str], Optional[str]]]

    def __hash__(self):
        # Use the id of the future as the hash since it's unique per operation
        return id(self.future)

    def __eq__(self, other):
        if not isinstance(other, BlockingOperation):
            return False
        return id(self.future) == id(other.future)


class BlockingQueueManager:
    """Manages blocking operations for list commands.

    This class is responsible for:
    1. Tracking clients waiting on specific keys
    2. Notifying waiting clients when data becomes available
    3. Handling timeouts for blocking operations
    """

    def __init__(self):
        """Initialize the BlockingQueueManager."""
        # Maps keys to sets of waiting operations
        self.waiting_operations: Dict[str, Set[BlockingOperation]] = defaultdict(set)

        # Track all active operations for cleanup
        self.active_operations: Set[BlockingOperation] = set()

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def wait_for_push(
        self, keys: List[str], timeout: float
    ) -> Tuple[Optional[str], Optional[str]]:
        """Wait for data to be pushed to any of the specified keys.

        Args:
            keys: List of keys to wait on
            timeout: Maximum time to wait in seconds (0 for no timeout)

        Returns:
            A tuple of (key, value) if data becomes available, or (None, None) on timeout
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        operation = BlockingOperation(
            event=asyncio.Event(),
            key=keys[0],  # Just track the first key for cleanup
            timeout=timeout,
            future=future,
        )

        async with self._lock:
            for key in keys:
                self.waiting_operations[key].add(operation)
            self.active_operations.add(operation)

        try:
            # Set up timeout if needed
            if timeout > 0:
                await asyncio.wait_for(operation.event.wait(), timeout=timeout)
            else:
                await operation.event.wait()

            if operation.event.is_set():
                return future.result()
            return None, None

        except asyncio.TimeoutError:
            return None, None

        finally:
            await self._cleanup_operation(operation, keys)

    async def notify_push(self, key: str, value: str) -> bool:
        """Notify any clients waiting on this key that data is available.

        Args:
            key: The key that received new data
            value: The value that was pushed

        Returns:
            bool: True if any clients were notified, False otherwise
        """
        async with self._lock:
            if key not in self.waiting_operations:
                return False

            # Get the first waiting operation (FIFO)
            operations = list(self.waiting_operations[key])
            if not operations:
                return False

            # Notify the first waiting client
            operation = operations[0]
            operation.future.set_result((key, value))
            operation.event.set()

            return True

    async def _cleanup_operation(
        self, operation: BlockingOperation, keys: List[str]
    ) -> None:
        """Clean up a completed or timed out operation."""
        async with self._lock:
            for key in keys:
                if operation in self.waiting_operations[key]:
                    self.waiting_operations[key].remove(operation)
                    if not self.waiting_operations[key]:
                        del self.waiting_operations[key]

            if operation in self.active_operations:
                self.active_operations.remove(operation)

    async def shutdown(self) -> None:
        """Cancel all pending operations during server shutdown."""
        async with self._lock:
            for operation in list(self.active_operations):
                operation.future.cancel()
                operation.event.set()

            self.waiting_operations.clear()
            self.active_operations.clear()
