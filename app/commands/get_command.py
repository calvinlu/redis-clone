"""This module implements the Redis GET command for retrieving values from the key-value store.

The GET command returns the value of a key. If the key does not exist, it returns nil.
"""

from typing import Any, Optional

from ..store import Store
from .base_command import Command


class GetCommand(Command):
    """Implementation of the Redis GET command.

    The GET command gets the given key from the store.
    """

    @property
    def name(self) -> str:
        return "GET"

    async def execute(self, *args: Any, store: Optional[Store] = None, **kwargs: Any):
        """Handle GET command by returning the value of the key saved in the store.

        Args:
            *args: Should contain the key as the first argument.
            store: The store instance to use for storage.
            **kwargs: Additional keyword arguments (not used).

        Returns:
            str: The string of the key.

        Raises:
            ValueError: If exactly 1 argument is provided or if store is not provided.
        """
        if len(args) != 1:
            raise ValueError("ERR wrong number of arguments for 'get' command")
        if store is None:
            raise ValueError("Store instance is required for GET command")
        key = str(args[0])
        return store.get_key(key)
