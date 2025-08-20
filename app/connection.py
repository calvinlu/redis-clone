"""Connection handling for Redis server.

This module provides functionality to handle incoming client connections,
parse commands, and dispatch them to appropriate command handlers.
"""

import asyncio
from typing import Any

from app.blocking.manager import BlockingManager
from app.commands.dispatcher import CommandDispatcher

# Import commands from their respective modules
from app.commands.echo_command import command as echo_command
from app.commands.list.llen_command import command as llen_command
from app.commands.list.lpop_command import command as lpop_command
from app.commands.list.lpush_command import command as lpush_command
from app.commands.list.lrange_command import command as lrange_command
from app.commands.list.rpush_command import command as rpush_command
from app.commands.ping_command import command as ping_command
from app.commands.string.get_command import command as get_command
from app.commands.string.set_command import command as set_command
from app.parser.parser import RESP2Parser
from app.resp2 import format_error, format_response
from app.store import Store


def create_dispatcher(
    store: Store, blocking_manager: BlockingManager
) -> CommandDispatcher:
    """Create and configure a command dispatcher with all available commands.

    Args:
        store: The store instance to be used by commands.
        blocking_manager: The blocking manager for handling blocking operations.

    Returns:
        CommandDispatcher: Configured dispatcher with all commands registered.
    """
    dispatcher = CommandDispatcher(store, blocking_manager)

    # Register all available commands
    dispatcher.register(ping_command)
    dispatcher.register(echo_command)
    dispatcher.register(set_command)
    dispatcher.register(get_command)
    dispatcher.register(rpush_command)
    dispatcher.register(lrange_command)
    dispatcher.register(lpush_command)
    dispatcher.register(llen_command)
    dispatcher.register(lpop_command)

    return dispatcher


async def _execute_command(
    dispatcher: CommandDispatcher, command: str, args: list
) -> Any:
    """Execute a command using the dispatcher and handle any errors.

    Args:
        dispatcher: CommandDispatcher instance for handling commands
        command: The command to execute
        args: List of arguments for the command

    Returns:
        The command response. For GET command, returns None for non-existent keys
        which will be formatted as a null bulk string ($-1\r\n).
    """
    try:
        # Execute the command and get the result
        result = await dispatcher.dispatch(command, *args)
        return result
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error executing command {command}: {e}")
        return format_error(str(e))


async def _send_response(writer: asyncio.StreamWriter, response: Any) -> bool:
    """Send a response to the client.

    Args:
        writer: StreamWriter for sending data to the client
        response: The response to send (will be formatted if not bytes)

    Returns:
        bool: True if the response was sent successfully, False otherwise
    """
    try:
        # Format the response if it's not already bytes
        if not isinstance(response, (bytes, bytearray)):
            response = format_response(response)

        # Write the response (could be None which is formatted as null bulk string)
        writer.write(response)
        await writer.drain()
        return True
    except (ConnectionError, asyncio.CancelledError) as e:
        print(f"Connection error while sending response: {e}")
        return False


async def _close_connection(writer: asyncio.StreamWriter, addr: str) -> None:
    """Safely close the connection.

    Args:
        writer: StreamWriter to close
        addr: Client address for logging
    """
    print(f"Closing connection from {addr}")
    try:
        writer.close()
        await writer.wait_closed()
    except (ConnectionError, asyncio.CancelledError) as e:
        print(f"Error while closing connection from {addr}: {e}")


async def handle_connection(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    dispatcher: CommandDispatcher,
    blocking_manager: BlockingManager,
) -> None:
    """Handle a new client connection.

    This coroutine is called for each new client connection. It reads commands
    from the client, processes them using the command dispatcher, and sends
    back responses.

    Args:
        reader: StreamReader for reading data from the client
        writer: StreamWriter for sending data to the client
        dispatcher: CommandDispatcher instance for handling commands
        blocking_manager: BlockingManager for handling blocking operations
    """
    addr = writer.get_extra_info("peername")
    print(f"New connection from {addr}")

    try:
        while True:
            try:
                # Read command from client
                data = await reader.read(1024)
                if not data:
                    break  # Connection closed by client

                # Parse the command
                parser = RESP2Parser(data)
                command, *args = parser.parse()

                # Execute the command
                response = await _execute_command(dispatcher, command.upper(), args)

                # Send the response
                if not await _send_response(writer, response):
                    break

            except ConnectionError as e:
                print(f"Connection error with {addr}: {e}")
                break
            except Exception as e:  # pylint: disable=broad-except
                print(f"Error handling command from {addr}: {e}")
                if not await _send_response(writer, format_error(str(e))):
                    break

    except asyncio.CancelledError:
        print(f"Connection from {addr} cancelled")
        raise
    except Exception as e:  # pylint: disable=broad-except
        print(f"Unexpected error with connection from {addr}: {e}")
    finally:
        await _close_connection(writer, addr)
