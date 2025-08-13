"""Base class for all store types."""
from abc import ABC, abstractmethod


class BaseStore(ABC):
    """Base class for all store types.

    All store implementations must inherit from this class and implement
    the required methods.
    """

    @abstractmethod
    def get_type(self) -> str:
        """Return the type name of this store.

        Returns:
            str: The type name (e.g., 'string', 'list')
        """

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a key from the store.

        Args:
            key: The key to delete

        Returns:
            bool: True if the key existed and was deleted, False otherwise
        """

    @abstractmethod
    def flushdb(self) -> None:
        """Delete all keys from the store."""
