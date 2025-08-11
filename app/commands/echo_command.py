"""Implementation of the Redis ECHO command.

This module provides functionality to handle the ECHO command, which returns
the message sent in the command. This is useful for testing if the connection
is working correctly and for measuring latency.
"""
from typing import Any

from .base_command import Command


class EchoCommand(Command):
    """Implementation of the Redis ECHO command.

    The ECHO command simply returns the message it receives.
    """

    @property
    def name(self) -> str:
        """Return the command name in uppercase."""
        return "ECHO"

    async def execute(self, *args: Any, **kwargs: Any) -> str:
        """Handle ECHO command by returning the input message.

        Args:
            *args: Should contain the message to echo as the first argument.

        Returns:
            str: The same message that was received, unchanged.

        Raises:
            ValueError: If no message is provided.
        """
        if not args:
            raise ValueError("ERR wrong number of arguments for 'echo' command")
        return str(args[0])


# Create a singleton instance of the command
command = EchoCommand()
