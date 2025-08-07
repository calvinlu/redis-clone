import asyncio

HOST = 'localhost'

PORT = 6379

PONG = b'+PONG\r\n'

async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    data = None

    while data != b'quit':
        writer.write(b'')
        await writer.drain()
        chunk = await reader.read(1024)
        if not chunk:
            break
        
        writer.write(PONG)
        await writer.drain()

    
async def run_server() -> None:
    server = await asyncio.start_server(handle_connection, HOST, PORT)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_server())
