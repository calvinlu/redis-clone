"""Implementation of the Redis ECHO command.

This module provides functionality to handle the ECHO command, which returns
the message sent in the command. This is useful for testing if the connection
is working correctly and for measuring latency.
"""

COMMAND = "echo"


async def handle_command(message: str) -> str:
    """Handle ECHO command by returning the input message.

    Args:
        message (str): The message to echo back.

    Returns:
        str: The same message that was received, unchanged.

    Note:
        This command is often used for testing if a connection is still alive,
        or to measure latency between the client and server.
    """
    return message
