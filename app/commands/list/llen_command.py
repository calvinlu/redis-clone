"""LLEN command for getting the length of a list."""
from typing import Any

from app.commands.base_command import Command


class LLenCommand(Command):
    """Handles the LLEN command for returning length of a list."""

    @property
    def name(self) -> str:
        """Returns the command name. Always in uppercase."""
        return "LLEN"

    async def execute(self, *args: Any, **kwargs: Any) -> int:
        """Executes the LLEN command.

        Args:
            *args: Command arguments where args[0] is the key and the rest are values to push.
            **kwargs: Additional keyword arguments, including 'store' for the store instance.

        Returns:
            int: The new length of the list after the push operation.

        Raises:
            TypeError: If no key or values are provided.
        """
        if len(args) != 1:
            raise ValueError("wrong number of arguments for 'rpush' command")

        store = kwargs.get("store")
        if not store:
            raise ValueError("store not provided in kwargs")

        key = args[0]
        # Use the llen method directly on the store, which will handle the list store internally
        return store.llen(key)


command = LLenCommand()
