"""Main entry point for the Redis server implementation.

This module initializes and runs the Redis-compatible server using asyncio.
"""

import asyncio

from store.store import Store

from app.connection import handle_connection

# Server configuration
HOST = "localhost"
PORT = 6379


async def run_server() -> None:
    """Run the Redis server.

    This function starts an asyncio server that handles incoming Redis client
    connections using the handle_connection callback.
    """
    server = await asyncio.start_server(
        lambda r, w: handle_connection(r, w, store), HOST, PORT
    )
    async with server:
        await server.serve_forever()


def main() -> None:
    """Entry point for the Redis server.

    Initializes the asyncio event loop and runs the server.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_server())
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        loop.close()


if __name__ == "__main__":
    main()
