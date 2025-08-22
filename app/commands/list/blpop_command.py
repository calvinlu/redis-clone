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

        return None

    async def _wait_for_element(
        self, store, keys: List[str], timeout: float
    ) -> Optional[List[str]]:
        """Wait for an element to be available in any of the given lists.

        This method uses asyncio events to efficiently wait for data to become
        available without busy-waiting. When a notification is received that data
        is available, it attempts to pop the value once.

        Args:
            store: The store instance
            keys: List of keys to wait on
            timeout: Maximum time to wait in seconds (0 for no timeout)

        Returns:
            [key, value] if an element became available, None on timeout
        """
        if not hasattr(store, "_blocking_queue_manager"):
            return None

        # First, try a non-blocking pop to see if data is already available
        result = await self._try_pop(store, keys)
        if result is not None:
            return result

        # If timeout is 0, return None immediately
        if timeout == 0:
            return None

        queue_manager = store._blocking_queue_manager
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        event = asyncio.Event()
        result = None

        async def try_pop_after_notification():
            nonlocal result
            try:
                # Wait for notification that data is available
                await event.wait()

                # After notification, try to get a value from any of the keys
                for key in keys:
                    if key in store.key_types and store.key_types[key] == "list":
                        value = store.lpop(key)
                        if value is not None and value != -1:
                            result = [key, str(value)]
                            if not future.done():
                                future.set_result(True)
                            return

                # If we get here, no value was found after notification
                if not future.done():
                    future.set_result(False)

            except Exception as e:
                if not future.done():
                    future.set_exception(e)

        # Define notification handler
        def on_notify(k: str, v: str):
            if not event.is_set():
                event.set()

        # Start the background task
        task = asyncio.create_task(try_pop_after_notification())

        # Register notification handlers for all keys
        for key in keys:
            await queue_manager.add_notification_handler(key, on_notify)

        try:
            # Wait for either the future to complete or the timeout to expire
            if timeout > 0:
                await asyncio.wait_for(future, timeout=timeout)
            else:
                await future

            return result

        except asyncio.TimeoutError:
            return None

        except asyncio.CancelledError:
            if not future.done():
                future.cancel()
            raise

        finally:
            # Clean up
            if not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass

            for key in keys:
                try:
                    await queue_manager.remove_notification_handler(key, on_notify)
                except Exception:
                    pass

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
        print(f"BLPOP execute called with args: {args}, kwargs: {kwargs}")
        self._validate_arguments(args, kwargs)
        store = kwargs["store"]
        timeout = float(args[-1])
        keys = list(args[:-1])
        print(f"BLPOP keys: {keys}, timeout: {timeout}")

        # Check for wrong type errors first
        self._check_wrong_type(store, keys)

        # If there are no lists to wait on, return None (will be serialized as null array)
        has_lists = any(
            key in store.key_types and store.key_types[key] == "list" for key in keys
        )
        print(f"BLPOP has_lists: {has_lists}")
        if not has_lists:
            # If timeout is 0, don't wait at all
            if timeout == 0:
                print("BLPOP no lists and timeout=0, returning None (null array)")
                return None
            # Otherwise, wait for a list to be created
            print("BLPOP waiting for list to be created...")
            result = await self._wait_for_element(store, keys, timeout)
            print(f"BLPOP after wait_for_element: {result}")
            return result  # Return None if no element was received

        # Try non-blocking pop first
        result = await self._try_pop(store, keys)
        print(f"BLPOP try_pop result: {result}")
        if result is not None:
            # Return as a list with key and value as strings
            return result  # Already in [key, value] string format

        # If timeout is 0, just return None (will be serialized as null array)
        if timeout == 0:
            print("BLPOP timeout=0, returning None (null array)")
            return None

        # Wait for an element to become available
        print("BLPOP waiting for element...")
        result = await self._wait_for_element(store, keys, timeout)
        print(f"BLPOP after wait_for_element: {result}")

        # Return the result or None if no element was received (will be serialized as null bulk string)
        return result

    async def _wait_for_blocking_pop(
        self, store: Any, keys: List[str], timeout: float
    ) -> Optional[List[str]]:
        """Wait for data to become available in any of the given lists.

        This is an alias for _wait_for_element for backward compatibility.
        """
        return await self._wait_for_element(store, keys, timeout)


# Create a singleton instance of the command
command = BLPopCommand()
