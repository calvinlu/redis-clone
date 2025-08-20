"""Base class for blocking Redis commands.

This module defines the BlockingCommand abstract base class that should be used
for commands that require BlockingManager functionality, such as BLPOP.
"""
from abc import abstractmethod
from typing import Any

from app.blocking.manager import BlockingManager
from app.store import Store

from .base_command import Command


class BlockingCommand(Command):
    """Base class for blocking Redis commands.

    Commands that need to perform blocking operations should inherit from this class
    instead of the base Command class. This provides access to the BlockingManager
    for implementing operations that wait for specific conditions.
    """

    @abstractmethod
    async def execute_blocking(
        self,
        store: Store,
        blocking_manager: BlockingManager,
        *args: str,
    ) -> Any:
        """Execute the blocking command.

        Args:
            store: The Redis store instance for data access.
            blocking_manager: The blocking manager for handling blocking operations.
            *args: Command arguments as strings.

        Returns:
            The command result, which will be converted to a RESP2 response.

        Raises:
            ValueError: If arguments are invalid or command execution fails.
        """
        raise NotImplementedError("Subclasses must implement execute_blocking()")

    async def execute(self, store: Store, *args: str) -> Any:
        """Execute the command (implements the base Command interface).

        This is a convenience method that raises an error if the blocking command
        is called without a BlockingManager. In normal operation, the dispatcher
        will call execute_blocking() directly.
        """
        raise RuntimeError(
            "BlockingCommand must be executed through a dispatcher with a BlockingManager"
        )
