"""Implementation of the Redis SET command.

This module provides functionality to handle the SET command, which sets the given
key to hold the specified string value. If the key already holds a value, it is
overwritten, regardless of its type.
"""

from app.store.store import Store

COMMAND = "set"


async def handle_command(key: str, value: str, store: Store) -> str:
    """Handle SET command by storing the key-value pair in the store.

    Args:
        key (str): The key under which to store the value.
        value (str): The value to store.
        store (Store): The store instance to use for storage.

    Returns:
        str: The string 'OK' to indicate success.

    Example:
        >>> store = Store()
        >>> await handle_command("mykey", "Hello", store)
        'OK'
    """
    store.set_key(key, value)
    return "OK"
