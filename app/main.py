"""Main entry point for the Redis server implementation.

This module initializes and runs the Redis-compatible server using asyncio.
"""

import asyncio
import signal
from typing import Tuple

from app.blocking import BlockingManager
from app.connection import create_dispatcher, handle_connection
from app.store import Store

# Server configuration
HOST = "localhost"
PORT = 6379


async def run_server() -> None:
    """Run the Redis server.

    This function starts an asyncio server that handles incoming Redis client
    connections using the handle_connection callback.
    """
    # Initialize the store and blocking manager
    store = Store()
    blocking_manager = BlockingManager()

    # Create command dispatcher with dependencies
    dispatcher = create_dispatcher(store, blocking_manager)

    # Create server with connection handler
    server = await asyncio.start_server(
        lambda r, w: handle_connection(r, w, dispatcher, blocking_manager),
        HOST,
        PORT,
    )

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    stop = asyncio.Future()
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    addr = server.sockets[0].getsockname() if server.sockets else "unknown"
    print(f"Server started on {addr}")

    try:
        async with server:
            # Run the server until the stop event is set
            await stop
            print("\nShutting down server...")
            # Cancel all blocking operations
            blocking_manager.cancel_all()
    except asyncio.CancelledError:
        print("\nServer shutdown requested...")
        blocking_manager.cancel_all()
        raise


def main() -> None:
    """Entry point for the Redis server.

    Initializes the asyncio event loop and runs the server.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(run_server())
    except KeyboardInterrupt:
        pass  # Handled by signal handler
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Cancel all running tasks
        tasks = [t for t in asyncio.all_tasks(loop=loop) if not t.done()]
        for task in tasks:
            task.cancel()

        # Run until all tasks are cancelled
        if tasks:
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

        # Close the loop
        loop.close()


if __name__ == "__main__":
    main()
