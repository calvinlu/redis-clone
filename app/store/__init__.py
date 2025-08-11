"""Redis key-value store implementation.

This package provides the core key-value storage functionality for the Redis server.
It includes the Store class that handles the in-memory storage of key-value pairs
with support for various Redis data types and operations.

Modules:
    - store: Contains the Store class implementation for key-value storage.
"""

# Import the Store class to make it available at the package level
from .store import Store  # noqa: F401

__all__ = ["Store"]
