"""A simple key-value store implementation.

This module provides a basic key-value store with get and set operations.
"""


class Store:
    """A simple key-value store class.

    This class provides basic key-value storage functionality with get and set operations.
    """

    def __init__(self):
        """Initialize a new Store instance with an empty dictionary."""
        self.store = {}

    def get_key(self, key: str) -> str:
        """
        Get the value of a key.

        Args:
            key: The key to get

        Returns:
            The value of the key. Returns None if key does not exist.
        """
        return self.store.get(key)

    def set_key(self, key: str, value: str) -> None:
        """
        Set the value of a key. If there is an existing key, overwrite it.

        Args:
            key: The key to set
            value: The value of the key to set

        Returns:
            The value of the saved key.
        """
        self.store[key] = str(value) if value is not None else ""
