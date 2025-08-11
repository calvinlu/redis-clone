"""Connection handling for Redis server.

This module provides functionality to handle incoming client connections,
parse commands, and dispatch them to appropriate command handlers.
"""

import asyncio

from app.commands import echo, ping
from app.commands import set as set_command
from app.parser.parser import RESP2Parser
from app.resp2 import format_error, format_response
from app.store.store import Store


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
                if command == b"PING":
                    response = await ping.handle_command()
                elif command == b"ECHO" and len(message) > 1:
                    # Convert message[1] to string if it's bytes
                    message_text = (
                        message[1].decode("utf-8")
                        if isinstance(message[1], bytes)
                        else message[1]
                    )
                    response = await echo.handle_command(message_text)
                elif command == b"SET" and len(message) > 2:
                    # Create store instance
                    store = Store()
                    key = (
                        message[1].decode("utf-8")
                        if isinstance(message[1], bytes)
                        else message[1]
                    )
                    value = (
                        message[2].decode("utf-8")
                        if isinstance(message[2], bytes)
                        else message[2]
                    )
                    response = await set_command.handle_command(key, value, store)
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
