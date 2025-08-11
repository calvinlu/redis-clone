import asyncio
from app.commands import ping, echo
from app.parser.parser import RESP2Parser

async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    parser = RESP2Parser(reader)
    data = None

    while data != b'quit':
        writer.write(b'')
        await writer.drain()
        
        message: parser.RESPValue =  await parser.parse()

        match message:
            case ping.COMMAND:
                writer.write(await ping.handle_command())
            case echo.COMMAND:
                echo_sound = message[1]
                writer.write(await echo.handle_command(echo_sound))
            
        await writer.drain()

        chunk = await reader.read(1024)
        print(f'chunk: {chunk}')
        print(f'chunk.decode(): {chunk.decode()}')
        print(f'chunk.decode().lower(): {chunk.decode().lower()}')

        if not chunk:
            break
        
        if 'ping' in chunk.decode().lower():
           writer.write(await ping.handle_command())
           await writer.drain()
