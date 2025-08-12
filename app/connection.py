"""Connection handling for Redis server.

This module provides functionality to handle incoming client connections,
parse commands, and dispatch them to appropriate command handlers.
"""

import asyncio
from typing import Any

from app.commands import (
    CommandDispatcher,
    echo_command,
    get_command,
    ping_command,
    set_command,
)
from app.parser.parser import RESP2Parser
from app.resp2 import format_error, format_response
from app.store import Store


def create_dispatcher(store: Store) -> CommandDispatcher:
    """Create and configure a command dispatcher with all available commands.

    Args:
        store: The store instance to be used by commands.

    Returns:
        CommandDispatcher: Configured dispatcher with all commands registered.
    """
    dispatcher = CommandDispatcher(store)

    # Register all available commands
    dispatcher.register(ping_command.command)
    dispatcher.register(echo_command.command)
    dispatcher.register(set_command.command)
    dispatcher.register(get_command.command)

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
        result = await dispatcher.execute(command, *args)
        # Return the result as-is to allow for proper RESP2 formatting
        # None will be formatted as null bulk string ($-1\r\n)

        return result
    except ValueError as e:
        return format_error(str(e))
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error executing command {command}: {e}")
        return format_error(f"ERR {str(e)}")


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
) -> None:
    """Handle a new client connection.

    This coroutine is called for each new client connection. It reads commands
    from the client, processes them using the command dispatcher, and sends
    back responses.

    Args:
        reader: StreamReader for reading data from the client
        writer: StreamWriter for sending data to the client
        dispatcher: CommandDispatcher instance for handling commands
    """
    parser = RESP2Parser(reader)
    addr = writer.get_extra_info("peername")
    print(f"New connection from {addr}")

    try:
        while True:
            try:
                print(f"[{addr}] Waiting for command...")
                # Parse the command
                command, args = await parser.parse_command()
                print(f"[{addr}] Received command: {command} with args: {args}")

                if not command:
                    print(f"[{addr}] Empty command, closing connection")
                    break

                # Execute command and get response
                print(f"[{addr}] Executing command...")
                response = await _execute_command(dispatcher, command, args)
                print(f"[{addr}] Command executed, response: {response!r}")

                # Send response if we have one
                print(f"[{addr}] Sending response...")
                if not await _send_response(writer, response):
                    print(f"[{addr}] Failed to send response")
                    break
                print(f"[{addr}] Response sent successfully")

            except asyncio.IncompleteReadError:
                print("Client disconnected")
                break
            except ConnectionResetError:
                print("Connection reset by peer")
                break
            except Exception as e:  # pylint: disable=broad-except
                print(f"Unexpected error with connection from {addr}: {e}")
                break

    except Exception as e:  # pylint: disable=broad-except
        print(f"Unexpected error with connection from {addr}: {e}")
    finally:
        await _close_connection(writer, addr)
