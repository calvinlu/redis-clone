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

        # Maps keys to sets of notification handlers
        self.notification_handlers: Dict[str, Set[callable]] = defaultdict(set)

        # Track all active operations for cleanup
        self.active_operations: Set[BlockingOperation] = set()

        # Create a lock that supports the context manager protocol
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
        if not keys:
            return None, None

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        operation = BlockingOperation(
            event=asyncio.Event(),
            key=keys[0],  # Just track the first key for cleanup
            timeout=timeout,
            future=future,
        )

        # If timeout is 0, don't wait
        if timeout == 0:
            return None, None

        # Store the start time for timeout calculation
        start_time = loop.time()

        async with self._lock:
            for key in keys:
                self.waiting_operations[key].add(operation)
            self.active_operations.add(operation)

        try:
            # Wait for the future to complete (set by _notify_operation)
            if timeout > 0:
                result = await asyncio.wait_for(future, timeout=timeout)
            else:
                result = await future

            return result if result is not None else (None, None)

        except asyncio.TimeoutError:
            return None, None

        except asyncio.CancelledError:
            # If the operation is cancelled, clean up and re-raise
            if not future.done():
                future.cancel()
            raise

        finally:
            await self._cleanup_operation(operation, keys)

    async def add_notification_handler(self, key: str, handler: callable) -> None:
        """Add a notification handler for a key.

        Args:
            key: The key to listen for notifications on
            handler: A callable that takes (key, value) as arguments
        """
        async with self._lock:
            self.notification_handlers[key].add(handler)

    async def remove_notification_handler(self, key: str, handler: callable) -> None:
        """Remove a notification handler for a key.

        Args:
            key: The key to stop listening for notifications on
            handler: The handler to remove
        """
        async with self._lock:
            if key in self.notification_handlers:
                self.notification_handlers[key].discard(handler)
                if not self.notification_handlers[key]:
                    del self.notification_handlers[key]

    async def _call_handler(self, handler: callable, key: str, value: str) -> None:
        """Call a notification handler with error handling."""
        try:
            handler(key, value)
        except Exception as e:
            print(f"Error in notification handler: {e}")

    async def notify_push(self, key: str, value: str) -> bool:
        """Notify one client waiting on this key that data is available.

        Args:
            key: The key that received new data
            value: The value that was pushed

        Returns:
            bool: True if a client was notified, False otherwise
        """
        # First, try to find a waiting operation to notify
        async with self._lock:
            if key in self.waiting_operations and self.waiting_operations[key]:
                # Find the first operation that's still waiting
                for operation in list(self.waiting_operations[key]):
                    if not operation.event.is_set() and not operation.future.done():
                        # Remove the operation from the waiting list
                        self.waiting_operations[key].remove(operation)
                        if not self.waiting_operations[key]:
                            del self.waiting_operations[key]

                        # Schedule the notification
                        asyncio.create_task(
                            self._notify_operation(operation, key, value)
                        )
                        return True

            # If no waiting operations, notify one notification handler
            if key in self.notification_handlers and self.notification_handlers[key]:
                # Get one handler
                handler = next(iter(self.notification_handlers[key]), None)
                if handler:
                    # Remove the handler so it's only called once
                    self.notification_handlers[key].remove(handler)
                    if not self.notification_handlers[key]:
                        del self.notification_handlers[key]

                    # Schedule the handler to be called
                    asyncio.create_task(self._call_handler(handler, key, value))
                    return True

        return False

    async def _notify_operation(
        self, operation: BlockingOperation, key: str, value: str
    ) -> None:
        """Notify a single operation that data is available."""
        try:
            if not operation.future.done():
                operation.future.set_result((key, value))
                operation.event.set()
        except Exception as e:
            print(f"Error notifying operation: {e}")
            # If there was an error, ensure the future is set to avoid hanging
            if not operation.future.done():
                operation.future.set_result((None, None))

    async def _cleanup_operation(
        self, operation: BlockingOperation, keys: List[str]
    ) -> None:
        """Clean up a completed or timed out operation."""
        async with self._lock:
            # Remove operation from all keys it was waiting on
            for key in list(self.waiting_operations.keys()):
                if operation in self.waiting_operations[key]:
                    self.waiting_operations[key].remove(operation)
                # Remove empty key sets
                if not self.waiting_operations[key]:
                    del self.waiting_operations[key]

            # Remove from active operations
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
