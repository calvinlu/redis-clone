"""Fixtures for end-to-end tests."""
import asyncio
import socket

import pytest

from app.connection import create_dispatcher, handle_connection
from app.store import Store

# Test server configuration
TEST_HOST = "127.0.0.1"


def get_available_port():
    """Find an available port for testing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((TEST_HOST, 0))
        return s.getsockname()[1]


@pytest.fixture
async def redis_server():
    """Fixture to start and stop a test Redis server."""
    # Create a new store and dispatcher for testing
    store = Store()
    dispatcher = create_dispatcher(store)

    # Start the server
    port = get_available_port()
    server = await asyncio.start_server(
        lambda r, w: handle_connection(r, w, dispatcher),
        host=TEST_HOST,
        port=port,
    )

    # Start the server in the background
    server_task = asyncio.create_task(server.serve_forever())

    # Return the server address and a cleanup function
    server_address = (TEST_HOST, port)

    yield server_address, store

    # Cleanup
    server_task.cancel()
    server.close()
    await server.wait_closed()


@pytest.fixture
async def redis_client(redis_server):
    """Fixture that provides a connected client to the test server."""
    server_address, _ = redis_server

    # Connect to the server
    reader, writer = await asyncio.open_connection(*server_address)

    yield reader, writer

    # Cleanup
    writer.close()
    await writer.wait_closed()
