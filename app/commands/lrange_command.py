"""A Redis-like key-value store with support for multiple data types.

This module provides a Store class that supports multiple data types (strings, lists, etc.)
while maintaining Redis's single-type-per-key semantics.
"""
from typing import Any, List

from app.commands.base_command import Command


class LRangeCommand(Command):
    """Handles the LRANGE command for returning a list splice"""

    @property
    def name(self) -> str:
        return "LRANGE"

    async def execute(self, *args: Any, **kwards: Any) -> List[str]:
        if len(args) < 3:
            raise ValueError("wrong number of arguments for 'lrange' command")

        store = kwards.get("store")
        if not store:
            raise ValueError("store not provided in kwargs")

        key = args[0]
        start = args[1]
        end = args[2]

        return store.lrange(key, start, end)
