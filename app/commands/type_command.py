"""Implementation of the Redis TYPE command.

"""
from typing import Any, Optional

from app.store import Store

from .base_command import Command


class TypeCommand(Command):
    """Implementation of the Redis TYPE command.

    The TYPE command is used to return the type of a given key.
    """

    @property
    def name(self) -> str:
        """Return the command name in uppercase."""
        return "TYPE"

    async def execute(
        self, *args: Any, store: Optional[Store] = None, **kwargs: Any
    ) -> str:
        """Handle TYPE command by returning the type of the given key

        Args:
            *args: Should contain the given key to check for type.
            store: The store instance to use for storage.

        Returns:
            str: The type of the given key. Returns "none" if key doesn't exist.
        """
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'type' command")
        return store.type(args[0])


command = TypeCommand()
