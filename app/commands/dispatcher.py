"""Command dispatcher for handling Redis commands.

This module provides the CommandDispatcher class which is responsible for
registering and executing Redis commands. It handles command lookup, argument
processing, and error handling.
"""
from typing import Any, Dict, Optional

from app.blocking import BlockingManager
from app.commands.base_command import Command
from app.commands.blocking_command import BlockingCommand
from app.store import Store


class CommandDispatcher:
    """Handles registration and execution of Redis commands.

    The CommandDispatcher maintains a registry of available commands and provides
    methods to execute them with proper argument handling and error management.
    """

    def __init__(self, store: Store, blocking_manager: BlockingManager):
        """Initialize the CommandDispatcher with store and blocking manager.

        Args:
            store: The store instance that all commands will use.
            blocking_manager: The blocking manager for handling blocking operations.
        """
        self.store = store
        self.blocking_manager = blocking_manager
        self.commands: Dict[str, Command] = {}

    def register(self, command: Command) -> None:
        """Register a command with the dispatcher.

        Args:
            command: The command instance to register.

        Raises:
            TypeError: If the command is not an instance of Command.
        """
        if not isinstance(command, Command):
            raise TypeError(f"Expected Command instance, got {type(command).__name__}")
        # Store command with uppercase name for case-insensitive matching
        self.commands[command.name.upper()] = command

    async def dispatch(self, command_name: str, *args: str) -> Any:
        """Execute a command with the given arguments.

        Args:
            command_name: The name of the command to execute.
            *args: Arguments to pass to the command.

        Returns:
            The result of the command execution.

        Raises:
            ValueError: If the command is not found.
        """
        command = self.commands.get(command_name.upper())
        if not command:
            raise ValueError(f"unknown command '{command_name}'")
        # If it's a blocking command, pass the blocking manager
        if isinstance(command, BlockingCommand):
            return await command.execute_blocking(
                self.store, self.blocking_manager, *args
            )
        # Otherwise, just pass the store
        return await command.execute(self.store, *args)

    async def execute(self, command_name: str, *args: str, **kwargs: Any) -> Any:
        """Alias for dispatch() for backward compatibility.

        This is kept for backward compatibility with existing code.
        New code should use dispatch() instead.
        """
        return await self.dispatch(command_name, *args)
