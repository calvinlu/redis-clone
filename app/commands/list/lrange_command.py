"""A Redis-like key-value store with support for multiple data types.

This module provides a Store class that supports multiple data types (strings, lists, etc.)
while maintaining Redis's single-type-per-key semantics.
"""
from typing import Any, List

from app.commands.base_command import Command


class LRangeCommand(Command):
    """Implementation of the LRANGE command.

    Returns the specified elements of the list stored at key.
    """

    @property
    def name(self) -> str:
        return "LRANGE"

    async def execute(self, *args: Any, **kwargs: Any) -> List[str]:
        if len(args) < 3:
            raise ValueError("wrong number of arguments for 'lrange' command")

        store = kwargs.get("store")
        if not store:
            raise ValueError("store not provided in kwargs")

        key = args[0]
        start = int(args[1])
        end = int(args[2])

        return store.lrange(key, start, end)


command = LRangeCommand()
