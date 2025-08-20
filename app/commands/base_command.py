"""Base class for all Redis command implementations.

This module defines the abstract base class that all Redis command implementations
must inherit from. It enforces a consistent interface for command execution.
"""
from abc import ABC, abstractmethod
from typing import Any

from app.store import Store


class Command(ABC):
    """Abstract base class for Redis command implementations.

    All Redis commands should inherit from this class and implement the execute
    method. The class provides a consistent interface for command execution and
    basic command metadata.
    """

    def __init__(self, name: str, arity: int, read_only: bool = False):
        """Initialize a new command instance.

        Args:
            name: The command name as it appears in the Redis protocol.
            arity: The number of arguments the command expects.
                  Positive means exact number of arguments.
                  Negative means minimum number of arguments, with last one being
                  treated as variadic.
            read_only: Whether the command is read-only (doesn't modify data).
        """
        self.name = name
        self.arity = arity
        self.read_only = read_only

    @abstractmethod
    async def execute(self, store: Store, *args: str) -> Any:
        """Execute the command with the given arguments.

        Args:
            store: The Redis store instance for data access.
            *args: Command arguments as strings.

        Returns:
            The command result, which will be converted to a RESP2 response.

        Raises:
            ValueError: If arguments are invalid or command execution fails.
        """
        raise NotImplementedError("Subclasses must implement execute()")
