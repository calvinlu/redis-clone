"""Connection handling for Redis server.

This module provides functionality to handle incoming client connections,
parse commands, and dispatch them to appropriate command handlers.
"""

import asyncio
from typing import Dict

from app.commands.base_command import Command
from app.commands.echo_command import EchoCommand
from app.commands.ping_command import PingCommand
from app.commands.set_command import SetCommand
from app.parser.parser import RESP2Parser
from app.resp2 import format_error, format_response
from app.store.store import Store

# Command registry mapping command names to their handler instances
COMMAND_REGISTRY: Dict[bytes, Command] = {
    b"PING": PingCommand(),
    b"ECHO": EchoCommand(),
    b"SET": SetCommand(),
}


async def handle_connection(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    """Handle a new client connection.

    This coroutine is called for each new client connection. It reads commands
    from the client, processes them, and sends back responses.

    Args:
        reader: StreamReader for reading data from the client
        writer: StreamWriter for sending data to the client
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

                # Convert command to bytes for comparison
                command = (
                    message[0].upper()
                    if isinstance(message, list) and len(message) > 0
                    else b""
                )

                # Process the command
                response = None
                command_handler = COMMAND_REGISTRY.get(command)

                if command_handler:
                    try:
                        # Convert message arguments to strings if they are bytes
                        args = [
                            arg.decode("utf-8") if isinstance(arg, bytes) else arg
                            for arg in message[1:]
                        ]

                        # Special case for commands that need the store
                        if command == b"SET":
                            store = Store()
                            response = await command_handler.execute(*args, store=store)
                        else:
                            response = await command_handler.execute(*args)

                    except ValueError as e:
                        response = format_error(str(e))
                    except Exception as e:  # pylint: disable=broad-except
                        print(f"Error executing command {command}: {e}")
                        response = format_error(f"ERR {str(e)}")
                else:
                    response = format_error("unknown command")

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
