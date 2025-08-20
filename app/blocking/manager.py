import asyncio
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Set, Tuple


class BlockingManager:
    """Manages blocking operations for Redis commands like BLPOP.

    This class tracks clients waiting for elements to be pushed to lists
    and notifies them when elements become available.
    """

    def __init__(self):
        # Maps list keys to a queue of waiting clients (futures)
        self.waiting_clients: Dict[str, Deque[asyncio.Future]] = defaultdict(deque)
        # Track active futures to prevent memory leaks
        self.active_futures: Set[asyncio.Future] = set()

    async def wait_for_pop(
        self, key: str, timeout: float = 0
    ) -> Optional[Tuple[str, str]]:
        """Wait for an element to be available in the list.

        Args:
            key: The list key to wait on
            timeout: Maximum time to wait in seconds (0 = no timeout)

        Returns:
            A tuple of (key, value) if an element is available, None if timed out
        """
        future = asyncio.get_running_loop().create_future()
        self.waiting_clients[key].append(future)
        self.active_futures.add(future)

        try:
            if timeout > 0:
                return await asyncio.wait_for(future, timeout=timeout)
            return await future
        except asyncio.TimeoutError:
            return None
        except asyncio.CancelledError:
            future.cancel()
            raise
        finally:
            self._cleanup_future(key, future)

    def notify_new_element(self, key: str, value: str) -> bool:
        """Notify waiting clients about a new element in the list.

        Args:
            key: The list key that received a new element
            value: The new element value

        Returns:
            bool: True if a client was notified, False otherwise
        """
        if not self.waiting_clients.get(key):
            return False

        # Get the oldest waiting future
        while self.waiting_clients[key]:
            future = self.waiting_clients[key].popleft()
            if not future.done():
                future.set_result((key, value))
                self.active_futures.discard(future)
                return True
            self.active_futures.discard(future)

        return False

    def _cleanup_future(self, key: str, future: asyncio.Future) -> None:
        """Clean up a future from the waiting clients and active futures."""
        if future in self.active_futures:
            self.active_futures.remove(future)

        if key in self.waiting_clients and future in self.waiting_clients[key]:
            self.waiting_clients[key].remove(future)

    def cancel_all(self) -> None:
        """Cancel all pending futures."""
        for future in self.active_futures:
            if not future.done():
                future.cancel()
        self.waiting_clients.clear()
        self.active_futures.clear()
