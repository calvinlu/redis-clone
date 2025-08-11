import asyncio
from app.commands import ping, echo
from app.parser.parser import RESP2Parser, encode

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
                
                # Process the command
                response = None
                if command == b'PING':
                    response = await ping.handle_command()
                elif command == b'ECHO' and len(message) > 1:
                    response = await echo.handle_command(message[1])
                else:
                    response = b"-ERR unknown command"
                
                # Send the response if we have one
                if response is not None:
                    writer.write(b"+" + response + b'\r\n')
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
