"""Base command class for Redis commands.

This module defines the base Command class that all Redis commands should inherit from.
"""
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union


class Command(ABC):
    """Abstract base class for Redis commands.

    All Redis commands should inherit from this class and implement the execute method.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the command name in uppercase.

        Returns:
            str: The command name in uppercase (e.g., 'PING', 'SET', 'GET').
        """
        pass

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Union[str, bytes, None]:
        """Execute the command with the given arguments.

        Args:
            *args: Positional arguments for the command.
            **kwargs: Keyword arguments for the command.

        Returns:
            The command result, which will be converted to a RESP2 response.

        Raises:
            Exception: If there's an error executing the command.
        """
        pass

    def __str__(self) -> str:
        """Return the command name for string representation."""
        return self.name
