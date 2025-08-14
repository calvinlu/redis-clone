"""Implementation of the Redis SET command.

This module provides functionality to handle the SET command, which sets the given
key to hold the specified string value. If the key already holds a value, it is
overwritten, regardless of its type.
"""
from typing import Any, Optional

from app.store.store import Store

from .base_command import Command


class SetCommand(Command):
    """Implementation of the Redis SET command.

    The SET command sets the given key to hold the specified string value.
    If the key already holds a value, it is overwritten.
    """

    @property
    def name(self) -> str:
        """Return the command name in uppercase."""
        return "SET"

    async def execute(
        self, *args: Any, store: Optional[Store] = None, **kwargs: Any
    ) -> str:
        """Handle SET command by storing the key-value pair in the store.

        Args:
            *args: Should contain the key as the first argument, value as the second,
                  and optionally 'PX' followed by TTL in milliseconds.
            store: The store instance to use for storage.
            **kwargs: Additional keyword arguments (not used).

        Returns:
            str: The string 'OK' to indicate success.

        Raises:
            ValueError: If arguments are invalid or store is not provided.
        """
        if len(args) < 2:
            raise ValueError(
                "ERR wrong number of arguments for 'set' command, expected 'SET key value [PX milliseconds]'"
            )

        if store is None:
            raise ValueError("ERR Store instance is required for SET command")

        key = str(args[0])
        value = str(args[1])
        ttl = None

        # Handle TTL if provided
        if len(args) >= 4 and args[2].upper() == "PX":
            try:
                ttl = int(args[3])
                if ttl <= 0:
                    raise ValueError("ERR invalid expire time in 'set' command")
            except (ValueError, TypeError) as exc:
                raise ValueError("ERR invalid expire time in 'set' command") from exc
        elif len(args) > 2:
            # If there are more than 2 arguments but not in PX format
            raise ValueError("ERR syntax error")

        store.set_key(key, value, ttl=ttl)
        return "OK"


# Create a singleton instance of the command
command = SetCommand()
