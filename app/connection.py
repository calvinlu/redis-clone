"""Connection handling for Redis server.

This module provides functionality to handle incoming client connections,
parse commands, and dispatch them to appropriate command handlers.
"""

import asyncio
from typing import Dict, Optional

from app.commands import (
    Command,
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
                # Parse the incoming message
                message = await parser.parse()
                print(f"Received message: {message}")

                if not message:
                    break

                # Extract command and arguments
                if not isinstance(message, list) or not message:
                    response = format_error("ERR invalid message format")
                    continue

                # Convert command name to string
                try:
                    command = (
                        message[0].decode("utf-8")
                        if isinstance(message[0], bytes)
                        else str(message[0])
                    )
                    # Convert args to strings
                    args = [
                        arg.decode("utf-8") if isinstance(arg, bytes) else str(arg)
                        for arg in (message[1:] if len(message) > 1 else [])
                    ]
                except (UnicodeDecodeError, AttributeError) as e:
                    response = format_error("ERR invalid command or arguments")
                    continue

                try:
                    # Dispatch the command to the appropriate handler
                    response = await dispatcher.execute(command, *args)
                except ValueError as e:
                    response = format_error(str(e))
                except Exception as e:  # pylint: disable=broad-except
                    print(f"Error executing command {command}: {e}")
                    response = format_error(f"ERR {str(e)}")

                # Send the response if we have one
                if response is not None:
                    try:
                        # Format the response if it's not already bytes
                        if not isinstance(response, (bytes, bytearray)):
                            response = format_response(response)
                        writer.write(response)
                        await writer.drain()
                    except (ConnectionError, asyncio.CancelledError) as e:
                        print(f"Connection error: {e}")
                        break

            except asyncio.IncompleteReadError:
                print("Client disconnected")
                break
            except ConnectionResetError:
                print("Connection reset by peer")
                break
            except Exception as e:  # pylint: disable=broad-except
                print(f"Unexpected error with connection from {addr}: {e}")
    except Exception as e:  # pylint: disable=broad-except
        print(f"Unexpected error with connection from {addr}: {e}")
    finally:
        print(f"Closing connection from {addr}")
        try:
            writer.close()
            await writer.wait_closed()
        except (ConnectionError, asyncio.CancelledError) as e:
            print(f"Error while closing connection from {addr}: {e}")
