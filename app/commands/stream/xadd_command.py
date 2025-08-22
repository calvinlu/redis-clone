"""Implementation of the Redis XADD command for adding entries to a stream."""
from typing import Any

from app.commands.base_command import Command
from app.store import Store


class XAddCommand(Command):
    """Handles the XADD command for adding entries to a stream."""

    @property
    def name(self) -> str:
        return "XADD"

    async def execute(self, *args: Any, **kwargs: Any) -> str:
        """Execute the XADD command.

        Args:
            *args: Command arguments where:
                - args[0] is the stream key
                - args[1] is the entry ID (explicit, not auto-generated)
                - Remaining args are field-value pairs
            **kwargs: Additional keyword arguments including 'store' for the store instance.

        Returns:
            str: The ID of the added entry.

        Raises:
            ValueError: For invalid arguments or conditions.
            TypeError: If the key exists but is not a stream.
        """
        if len(args) < 3:
            raise ValueError("ERR wrong number of arguments for 'xadd' command")

        store = kwargs.get("store")
        if not store or not isinstance(store, Store):
            raise ValueError("store not provided in kwargs or invalid store instance")

        key = args[0]
        if not key:
            raise ValueError("ERR Invalid stream key")

        entry_id = args[1]
        field_value_pairs = args[2:]

        # Ensure we have field-value pairs and they're in pairs
        if not field_value_pairs or len(field_value_pairs) % 2 != 0:
            raise ValueError("ERR wrong number of arguments for 'xadd' command")

        # Convert field-value pairs to a dictionary
        field_value_dict = dict(zip(field_value_pairs[::2], field_value_pairs[1::2]))

        try:
            # Call store.xadd with the key, entry_id, and field-value pairs as keyword arguments
            return store.xadd(key, entry_id, **field_value_dict)
        except TypeError as e:
            raise TypeError(
                "WRONGTYPE Operation against a key holding the wrong kind of value"
            ) from e


# Create a singleton instance of the command
command = XAddCommand()
