"""Implementation of the Redis BLPOP command."""
import asyncio
from typing import Any, List, Optional, Union

from app.commands.base_command import Command
from app.parser.parser import NullArray
from app.resp2.types import Error


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
                raise ValueError("timeout is negative")
        except (ValueError, TypeError) as e:
            if "negative" in str(e).lower():
                raise ValueError("timeout is negative") from e
            raise ValueError("timeout is not a float") from e

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

    async def _try_pop(self, store, keys: List[str]) -> Union[List[str], NullArray]:
        """Try to pop an element from any of the given keys.

        Returns:
            List with [key, value] if successful, NullArray otherwise
        """
        for key in keys:
            if key not in store.key_types:
                continue

            if store.key_types[key] != "list":
                continue

            # Try to pop from the left
            value = store.lpop(key)

            # Check if we got a valid value
            if (
                value is not None and value != -1
            ):  # -1 means key doesn't exist or list is empty
                # Convert the value to a string if it's not already
                str_value = str(value)
                if str_value:  # Make sure it's not an empty string
                    # Return as a list with key and value
                    return [key, str_value]

                # If we got an empty string, continue to next key
                continue

            # If list is empty after pop, remove the key if needed
            if key in store.key_types and store.key_types[key] == "list":
                if store.llen(key) == 0:
                    store.delete(key)

        return NullArray()

    async def _wait_for_element(
        self, store, keys: List[str], timeout: float
    ) -> Union[List[str], NullArray]:
        """Wait for an element to be available in any of the given lists.

        This method uses asyncio events to efficiently wait for data to become
        available without busy-waiting. When a notification is received that data
        is available, it attempts to pop the value once.

        Args:
            store: The store instance
            keys: List of keys to wait on
            timeout: Maximum time to wait in seconds (0 for no timeout)

        Returns:
            [key, value] if an element became available, NullArray on timeout
        """
        # First, try a non-blocking pop to see if data is already available
        result = await self._try_pop(store, keys)
        if not isinstance(result, NullArray):
            return result

        # If timeout is 0, return NullArray immediately
        if timeout == 0:
            return NullArray()

        # If we don't have a queue manager, just wait the timeout and check again
        if not hasattr(store, "_blocking_queue_manager"):
            await asyncio.sleep(timeout)
            result = await self._try_pop(store, keys)
            return result if not isinstance(result, NullArray) else NullArray()

        queue_manager = store._blocking_queue_manager
        event = asyncio.Event()
        result = None

        # Define notification handler
        def on_notify(k: str, v: str):
            if not event.is_set():
                event.set()

        # Register notification handlers for all keys
        for key in keys:
            await queue_manager.add_notification_handler(key, on_notify)

        try:
            # Wait for either notification or timeout
            try:
                # Wait for the full timeout or until we get a notification
                await asyncio.wait_for(event.wait(), timeout=timeout)
                # If we get here, we got a notification - try to pop
                result = await self._try_pop(store, keys)
                if not isinstance(result, NullArray):
                    return result
            except asyncio.TimeoutError:
                # If we timed out, just continue to return NullArray
                pass

            # Final check before returning
            result = await self._try_pop(store, keys)
            return result if not isinstance(result, NullArray) else NullArray()

        finally:
            # Clean up notification handlers
            for key in keys:
                if hasattr(queue_manager, "remove_notification_handler"):
                    await queue_manager.remove_notification_handler(key, on_notify)
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass

    async def _wait_for_blocking_pop(
        self, store: Any, keys: List[str], timeout: float
    ) -> Optional[List[str]]:
        """Wait for data to become available in any of the given lists.

        This is an alias for _wait_for_element for backward compatibility.
        """
        return await self._wait_for_element(store, keys, timeout)

    async def execute(
        self, *args: Any, **kwargs: Any
    ) -> Union[List[str], NullArray, Error]:
        """Executes the BLPOP command.

        Args:
            *args: Command arguments where:
                - args[:-1]: List of keys to check
                - args[-1]: Timeout in seconds (0 for infinite wait)
            **kwargs: Additional keyword arguments:
                - store: The data store instance (required)

        Returns:
            - If an element was popped: [key, value]
            - If timeout was reached or no element was found: NullArray

        Raises:
            ValueError: If arguments are invalid or store is not provided
            TypeError: If any key exists but is not a list
        """
        try:
            print(f"BLPOP execute called with args: {args}, kwargs: {kwargs}")
            self._validate_arguments(args, kwargs)
            store = kwargs["store"]
            keys = list(args[:-1])  # All args except the last one are keys
            timeout = float(args[-1])  # Last arg is the timeout

            print(f"BLPOP keys: {keys}, timeout: {timeout}")

            # Check for wrong type before proceeding
            self._check_wrong_type(store, keys)

            # Check if any keys exist and are lists
            has_lists = any(
                key in store.key_types and store.key_types[key] == "list"
                for key in keys
            )

            print(f"BLPOP has_lists: {has_lists}")
            if not has_lists:
                # If timeout is 0, don't wait at all
                if timeout == 0:
                    print("BLPOP no lists and timeout=0, returning NullArray")
                    return NullArray()
                # Otherwise, wait for a list to be created
                print("BLPOP waiting for list to be created...")
                result = await self._wait_for_element(store, keys, timeout)
                print(f"BLPOP after wait_for_element: {result}")
                return result

            # If we have lists, try to pop immediately
            result = await self._try_pop(store, keys)
            if not isinstance(result, NullArray):
                return result

            # If we have lists but they're empty, wait for an element
            if timeout > 0:
                result = await self._wait_for_element(store, keys, timeout)
                return result if not isinstance(result, NullArray) else NullArray()

            return NullArray()

        except Exception as e:
            print(f"BLPOP error: {e}")
            return NullArray()
        return result if result is not None else NullArray()

    async def _wait_for_blocking_pop(
        self, store: Any, keys: List[str], timeout: float
    ) -> Optional[List[str]]:
        """Wait for data to become available in any of the given lists.

        This is an alias for _wait_for_element for backward compatibility.
        """
        return await self._wait_for_element(store, keys, timeout)


# Create a singleton instance of the command
command = BLPopCommand()
