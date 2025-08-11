import asyncio
from typing import Any, List, Union

from app.commands import ping, echo
from app.parser.parser import RESP2Parser
from app.resp2 import format_response, format_error

async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    parser = RESP2Parser(reader)
    addr = writer.get_extra_info('peername')
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
                command = message[0].upper() if isinstance(message, list) and len(message) > 0 else b''
                
                try:
                    # Process the command
                    response = None
                    if command == b'PING':
                        response = await ping.handle_command()
                    elif command == b'ECHO' and len(message) > 1:
                        # Convert message[1] to string if it's bytes
                        message_text = message[1].decode('utf-8') if isinstance(message[1], bytes) else message[1]
                        response = await echo.handle_command(message_text)
                    else:
                        response = format_error("unknown command")
                    
                    # Send the response if we have one
                    if response is not None:
                        # Format the response if it's not already bytes
                        if not isinstance(response, (bytes, bytearray)):
                            response = format_response(response)
                        writer.write(response)
                        await writer.drain()
                        
                except Exception as e:
                    print(f"Error processing command: {e}")
                    writer.write(format_error(f"Error: {str(e)}"))
                    await writer.drain()
                
            except asyncio.IncompleteReadError:
                print("Client disconnected")
                break
            except ConnectionResetError:
                print("Connection reset by peer")
                break
            except Exception as e:
                print(f"Error handling connection: {e}")
                writer.write(b"-ERR internal error\r\n")
                await writer.drain()
                break
                
    finally:
        print(f"Closing connection from {addr}")
        writer.close()
        await writer.wait_closed()
