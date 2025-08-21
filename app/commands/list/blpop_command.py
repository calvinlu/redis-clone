"""Implementation of the Redis BLPOP command."""
from typing import Any, Dict, List, Optional, Tuple, Union

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

    async def execute(self, *args: Any, **kwargs: Any) -> Union[str, List[str], None]:
        """Executes the BLPOP command.

        BLPOP is a blocking list pop primitive. It is the blocking version of LPOP because it blocks the
        connection when there are no elements to pop from any of the given lists. An element is popped
        from the head of the first list that is non-empty, with the given keys being checked in the
        order that they are given.

        Args:
            *args: Command arguments where:
                - args[:-1]: List of keys to check
                - args[-1]: Timeout in seconds (0 for non-blocking)
            **kwargs: Additional keyword arguments:
                - store: The data store instance (required)

        Returns:
            - If an element was popped: [key, value]
            - If timeout was reached: None (formatted as null array in RESP)

        Raises:
            ValueError: If arguments are invalid, store is not provided, or timeout is invalid
            TypeError: If any key exists but is not a list
        """
        self._validate_arguments(args, kwargs)
        store = kwargs["store"]
        timeout = float(args[-1])
        keys = list(args[:-1])

        # Try non-blocking pop first
        result = await self._try_non_blocking_pop(store, keys)
        if result is not None:
            return result

        # If non-blocking and no data, return immediately
        if timeout == 0:
            return None

        # Block and wait for data
        return await self._wait_for_blocking_pop(store, keys, timeout)

    def _validate_arguments(
        self, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> None:
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
