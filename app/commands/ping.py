"""Implementation of the Redis PING command.

This module provides functionality to handle the PING command, which is used
to test if a connection is still alive, measure latency, or just test if the
server is available.
"""

COMMAND = "ping"


async def handle_command() -> str:
    """Handle PING command by returning 'PONG'.

    Returns:
        str: The string 'PONG' as specified by the Redis protocol.
    """
    return "PONG"
