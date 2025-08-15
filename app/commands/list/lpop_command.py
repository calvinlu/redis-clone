"""LPOP command for removing and returning first element of a list."""
from typing import Any

from app.commands.base_command import Command


class LPopCommand(Command):
    """Handles the LPOP command for removing and returning the front element of a list."""

    @property
    def name(self) -> str:
        return "LPOP"

    async def execute(self, *args: Any, **kwargs: Any) -> int:
        """Executes the LPUSH command.

        Args:
            *args: Command arguments where args[0] is the key and the rest are values to push.
            **kwargs: Additional keyword arguments, including 'store' for the store instance.

        Returns:
            int: The new length of the list after the push operation.

        Raises:
            TypeError: If no key or values are provided.
        """
        if len(args) not in [1, 2]:
            raise ValueError("wrong number of arguments for 'lpop' command")

        store = kwargs.get("store")
        key = args[0]
        try:
            count = int(args[1]) if len(args) == 2 else None
        except ValueError as e:
            raise ValueError("number of elements to lpop should be int") from e

        return store.lpop(key, count)


command = LPopCommand()
