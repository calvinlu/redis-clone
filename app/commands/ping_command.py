"""Implementation of the Redis PING command.

This module provides functionality to handle the PING command, which is used
to test if a connection is still alive, measure latency, or just test if the
server is available.
"""
from .base_command import Command


class PingCommand(Command):
    """Implementation of the Redis PING command.

    The PING command is used to test if a connection is still alive.
    """

    @property
    def name(self) -> str:
        """Return the command name in uppercase."""
        return "PING"

    async def execute(self, *args, **kwargs) -> str:
        """Handle PING command by returning 'PONG'.

        Returns:
            str: The string 'PONG' as specified by the Redis protocol.
        """
        return "PONG"


# Create a singleton instance of the command
command = PingCommand()
