"""Implementation of the Redis BLPOP command."""
from typing import Any, List, Union

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

        Args:
            *args: Command arguments where args[:-1] are the keys and args[-1] is the timeout.
            **kwargs: Additional keyword arguments, including 'store' for the store instance.

        Returns:
            - If an element was popped: [key, value]
            - If timeout was reached: None

        Raises:
            ValueError: If arguments are invalid or store is not provided.
            TypeError: If any key exists but is not a list.
        """
        if len(args) < 2:
            raise ValueError("wrong number of arguments for 'blpop' command")

        store = kwargs.get("store")
        if not store:
            raise ValueError("store not provided in kwargs")

        try:
            # Parse timeout (convert from seconds to float)
            timeout = float(args[-1])
            if timeout < 0:
                raise ValueError("timeout is negative")

            keys = list(args[:-1])

            # First, try a non-blocking pop from any of the lists
            for key in keys:
                if key in store.key_types:
                    if store.key_types[key] != "list":
                        raise TypeError(
                            f"WRONGTYPE Operation against a key holding the wrong kind of value: {key}"
                        )

                    # Get the list store
            list_store = store._get_or_create_store(
                "list"
            )  # pylint: disable=protected-access
            # Try to pop from the list
            value = list_store.lpop(key)
            if value is not None:
                return [key, value]

            # If we get here, all lists are empty - wait for data
            if timeout == 0:  # Non-blocking
                return None

            # Make sure we have the list store created
            list_store = store._get_or_create_store(
                "list"
            )  # pylint: disable=protected-access

            # Block until data is available or timeout
            key, value = await store._blocking_queue_manager.wait_for_push(
                keys, timeout
            )  # pylint: disable=protected-access
            if key is not None and value is not None:
                # Get the list store and pop the value
                list_store.lpop(key)
                return [key, value]

            return None

        except (ValueError, TypeError) as e:
            if "WRONGTYPE" in str(e):
                raise
            if "timeout is negative" in str(e):
                raise
            raise ValueError("timeout is not a float or out of range") from e


# Create a singleton instance of the command
command = BLPopCommand()
