"""Command dispatcher for handling Redis commands.

This module provides the CommandDispatcher class which is responsible for
registering and executing Redis commands. It handles command lookup, argument
processing, and error handling.
"""
from typing import Any, Dict

from app.commands.base_command import Command
from app.store import Store


class CommandDispatcher:
    """Handles registration and execution of Redis commands.

    The CommandDispatcher maintains a registry of available commands and provides
    methods to execute them with proper argument handling and error management.
    It's responsible for:
    - Maintaining the command registry
    - Routing commands to their handlers
    - Handling basic command validation
    - Standardizing error handling
    """

    def __init__(self, store: Store):
        """Initialize the CommandDispatcher with a store instance.

        Args:
            store: The store instance that all commands will use.
        """
        self.store = store
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

    async def execute(self, command_name: str, *args: str, **kwargs: Any) -> str:
        """Execute a command with the given arguments.

        Args:
            command_name: The name of the command to execute (case-insensitive).
            *args: String arguments passed to the command.
            **kwargs: Additional keyword arguments to pass to the command.

        Returns:
            str: The string result of the command execution.

        Raises:
            ValueError: If the command is not found or arguments are invalid.
        """
        # Convert command name to uppercase for case-insensitive matching
        command_key = command_name.upper()
        command = self.commands.get(command_key)
        if not command:
            raise ValueError(f"unknown command '{command_name}'")

        try:
            # Execute the command with the store and any additional kwargs
            result = await command.execute(*args, store=self.store, **kwargs)
            # Return the result as-is to allow for proper RESP2 formatting
            # (e.g., None should be formatted as '$-1\r\n' for nil responses)
            return result
        except Exception as e:
            # Re-raise the exception with a more descriptive message
            raise ValueError(f"ERR {str(e)}") from e
