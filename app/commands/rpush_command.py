"""RPUSH command for pushing elements to a list."""
from typing import Any

from app.commands.base_command import Command


class RPushCommand(Command):
    """Handles the RPUSH command for pushing elements to the end of a list."""

    @property
    def name(self) -> str:
        """Returns the command name, always in uppercase."""
        return "RPUSH"

    async def execute(self, *args: Any, **kwargs: Any) -> int:
        """Executes the RPUSH command.

        Args:
            *args: Command arguments where args[0] is the key and the rest are values to push.
            **kwargs: Additional keyword arguments, including 'store' for the store instance.

        Returns:
            int: The new length of the list after the push operation.

        Raises:
            TypeError: If no key or values are provided.
        """
        if len(args) < 2:
            raise TypeError("wrong number of arguments for 'rpush' command")

        store = kwargs.get("store")
        if not store:
            raise ValueError("store not provided in kwargs")

        key = args[0]
        values = args[1:]
        return store.list_store.rpush(key, *values)


# Create a singleton instance of the command
command = RPushCommand()
