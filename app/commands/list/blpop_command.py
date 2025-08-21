"""Implementation of the Redis BLPOP command."""
import asyncio
from typing import Any, List, Optional, Union

from app.commands.base_command import Command


class BLPopCommand(Command):
    """Handles the BLPOP command for blocking list pops with timeout.

    BLPOP is a blocking list pop primitive. It is the blocking version of LPOP
    because it blocks the connection when there are no elements to pop from
    any of the given lists. An element is popped from the head of the first
    list that is non-empty, with the given keys being checked in the order
    that they are given.
    """

    @property
    def name(self) -> str:
        """Returns the command name, always in uppercase."""
        return "BLPOP"

    def _validate_arguments(self, args: tuple, kwargs: dict) -> None:
        """Validate command arguments."""
        if len(args) < 2:
            raise ValueError("wrong number of arguments for 'BLPOP' command")
        if "store" not in kwargs:
            raise ValueError("store is required")
        try:
            timeout = float(args[-1])
            if timeout < 0:
                raise ValueError("timeout can't be negative")
        except (ValueError, TypeError) as e:
            raise ValueError("timeout is not a valid float") from e

    def _is_list_key(self, store, key: str) -> bool:
        """Check if a key exists and is a list."""
        return key in store.key_types and store.key_types[key] == "list"

    def _check_wrong_type(self, store, keys: List[str]) -> None:
        """Check if any key exists with a non-list type."""
        for key in keys:
            if key in store.key_types and store.key_types[key] != "list":
                raise TypeError(
                    f"WRONGTYPE Operation against a key holding the wrong kind of value: {key}"
                )

    async def _try_pop(self, store, keys: List[str]) -> Optional[List[str]]:
        """Try to pop an element from any of the given keys.

        Returns:
            List with [key, value] if successful, None otherwise
        """
        for key in keys:
            if key not in store.key_types:
                continue

            if store.key_types[key] != "list":
                continue

            # Try to pop from the left
            value = store.lpop(key)
            if value is not None:
                return [key, value]
        return None

    async def execute(self, *args: Any, **kwargs: Any) -> Union[bytes, None]:
        """Executes the BLPOP command.

        Args:
            *args: Command arguments where:
                - args[:-1]: List of keys to check
                - args[-1]: Timeout in seconds (0 for infinite wait)
            **kwargs: Additional keyword arguments:
                - store: The data store instance (required)

        Returns:
            - If an element was popped: [key, value]
            - If timeout was reached: None

        Raises:
            ValueError: If arguments are invalid or store is not provided
            TypeError: If any key exists but is not a list
        """
        self._validate_arguments(args, kwargs)
        store = kwargs["store"]
        timeout = float(args[-1])
        keys = list(args[:-1])

        # Check for wrong type errors first
        self._check_wrong_type(store, keys)

        # Try non-blocking pop first
        result = await self._try_pop(store, keys)
        if result is not None:
            return result

        # If timeout is 0, we should block indefinitely
        # Use a short timeout and loop to allow for proper cancellation
        if timeout == 0:
            timeout = 0.1  # Short timeout for responsiveness

        # Otherwise, wait for data with timeout
        try:
            # Use a shorter sleep interval for more responsive behavior
            sleep_interval = 0.01  # 10ms
            total_waited = 0.0

            while True:
                # Try to pop an element
                result = await self._try_pop(store, keys)
                if result is not None:
                    return result

                # Check if we've exceeded the timeout
                if timeout > 0 and total_waited >= timeout:
                    return None

                # Small sleep to prevent busy waiting
                await asyncio.sleep(sleep_interval)
                if timeout > 0:  # Only increment if we have a timeout
                    total_waited += sleep_interval

        except asyncio.CancelledError:
            return None

    def _validate_arguments(self, args: tuple, kwargs: dict) -> None:
        """Validate BLPOP command arguments."""
        if len(args) < 2:
            raise ValueError("wrong number of arguments for 'blpop' command")
        if "store" not in kwargs:
            raise ValueError("store not provided in kwargs")
        try:
            timeout = float(args[-1])
            if timeout < 0:
                raise ValueError("timeout is negative")
        except (ValueError, TypeError) as e:
            if "could not convert" in str(e).lower():
                raise ValueError("timeout is not a float or out of range") from e
            raise

    async def _try_non_blocking_pop(
        self, store: Any, keys: List[str]
    ) -> Optional[List[str]]:
        """Attempt to pop an element from any of the given lists without blocking.

        Returns:
            [key, value] if an element was popped, None otherwise
        """
        for key in keys:
            if key in store.key_types and store.key_types[key] != "list":
                raise TypeError(
                    f"WRONGTYPE Operation against a key holding the wrong kind of value: {key}"
                )

            list_store = store.get_list_store()
            value = list_store.lpop(key)
            if value is not None:
                return [key, value]
        return None

    async def _wait_for_blocking_pop(
        self, store: Any, keys: List[str], timeout: float
    ) -> Optional[List[str]]:
        """Wait for data to become available in any of the given lists.

        Args:
            store: The data store instance
            keys: List of keys to wait on
            timeout: Maximum time to wait in seconds

        Returns:
            [key, value] if data was received, None on timeout
        """
        list_store = store.get_list_store()
        key, value = await list_store.queue_manager.wait_for_push(keys, timeout)
        if key is None or value is None:
            return None
        # Remove the item from the list
        list_store.lpop(key)
        return [key, value]


# Create a singleton instance of the command
command = BLPopCommand()
