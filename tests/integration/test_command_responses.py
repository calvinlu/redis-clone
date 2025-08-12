"""End-to-end tests for Redis command responses.

These tests verify that commands return the correct RESP2 formatted responses.
"""
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


class TestCommandResponses:
    """Test that commands return properly formatted RESP2 responses."""

    @pytest.fixture
    async def redis_server(self):
        """Fixture to start and stop a test Redis server."""
        # Create a new store and dispatcher for testing
        store = Store()
        dispatcher = create_dispatcher(store)

        # Get an available port
        port = get_available_port()

        # Create server with the app's handle_connection
        server = await asyncio.start_server(
            lambda r, w: handle_connection(r, w, dispatcher),
            TEST_HOST,
            port,
        )

        # Store the port for use in tests
        server.port = port

        async with server:
            server_task = asyncio.create_task(server.serve_forever())
            try:
                yield server
            finally:
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass

    @pytest.fixture
    async def redis_client(self, redis_server):
        """Fixture to provide a connected Redis client."""
        reader, writer = await asyncio.open_connection(TEST_HOST, redis_server.port)
        try:
            yield reader, writer
        finally:
            writer.close()
            await writer.wait_closed()

    def format_command(self, *args):
        """Format command arguments according to RESP2 protocol."""
        command = f"*{len(args)}\r\n"
        for arg in args:
            arg = str(arg)
            command += f"${len(arg)}\r\n{arg}\r\n"
        return command

    async def send_command(self, reader, writer, *args):
        """Helper to send a command and return the raw response.

        Args:
            reader: The StreamReader to read the response from
            writer: The StreamWriter to write the command to
            *args: Command and its arguments (e.g., 'SET', 'key', 'value')

        Returns:
            The raw response from the server
        """
        command = self.format_command(*args)
        writer.write(command.encode())
        await writer.drain()
        return await reader.read(1024)

    @pytest.mark.asyncio
    async def test_ping_command(self, redis_client):
        """Test that PING returns the correct response."""
        reader, writer = redis_client
        response = await self.send_command(reader, writer, "PING")
        assert response == b"+PONG\r\n"

    @pytest.mark.asyncio
    async def test_get_set_commands(self, redis_client):
        """Test basic GET/SET command flow."""
        reader, writer = redis_client

        # Test SET
        response = await self.send_command(reader, writer, "SET", "mykey", "myvalue")
        assert response == b"+OK\r\n"

        # Test GET
        response = await self.send_command(reader, writer, "GET", "mykey")
        assert response == b"+myvalue\r\n"

        # Test GET non-existent key
        response = await self.send_command(reader, writer, "GET", "nonexistent")
        assert response == b"+\r\n"  # Empty string response for non-existent keys

    @pytest.mark.asyncio
    async def test_expiration(self, redis_client):
        """Test that keys with TTL expire correctly."""
        reader, writer = redis_client

        # Set key with short TTL (100ms)
        response = await self.send_command(
            reader, writer, "SET", "temp_key", "temp_value", "PX", "100"
        )
        assert response == b"+OK\r\n"

        # Should still exist
        response = await self.send_command(reader, writer, "GET", "temp_key")
        assert response == b"+temp_value\r\n"

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Should be expired (returns empty string)
        response = await self.send_command(reader, writer, "GET", "temp_key")
        assert response == b"+\r\n"  # Empty string response for expired keys

    @pytest.mark.asyncio
    async def test_invalid_command(self, redis_client):
        """Test that invalid commands return an error."""
        reader, writer = redis_client
        response = await self.send_command(reader, writer, "NOSUCHCOMMAND")
        assert response.startswith(b"-unknown command")

    @pytest.mark.asyncio
    async def test_wrong_number_of_arguments(self, redis_client):
        """Test that commands with wrong number of arguments return an error."""
        reader, writer = redis_client
        response = await self.send_command(reader, writer, "GET")
        assert b"wrong number of arguments" in response


# This allows running the tests with: python -m pytest tests/integration/test_command_responses.py -v
if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main(["-v", __file__]))
