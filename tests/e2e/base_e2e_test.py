"""Base class for end-to-end tests using redis-py client."""
import os
import subprocess
import time
from typing import Any, Optional

import pytest
from redis.asyncio import Redis

# Get the server port from environment or use default
TEST_PORT = int(os.environ.get("TEST_PORT", "6379"))
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")


class BaseE2ETest:
    """Base class for end-to-end tests that need a running Redis server."""

    _server_process: Optional[subprocess.Popen] = None
    _test_client: Optional[Redis] = None

    @classmethod
    def setup_class(cls):
        """Start the test server before any tests in this class run."""
        # Start the server in a separate process
        cls._server_process = subprocess.Popen(
            ["python", "-m", "app.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"PYTHONPATH": ".", **os.environ},
        )

        # Give the server time to start
        time.sleep(1)

    @classmethod
    def teardown_class(cls):
        """Stop the test server after all tests in this class run."""
        if cls._test_client:
            cls._test_client.close()
        if cls._server_process:
            cls._server_process.terminate()
            try:
                cls._server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls._server_process.kill()

    @pytest.fixture(autouse=True)
    async def setup_client(self):
        """Set up a fresh Redis client for each test."""
        self._test_client = Redis(
            host=SERVER_HOST, port=TEST_PORT, decode_responses=True
        )
        yield
        # Clean up
        await self._test_client.aclose()
        await self._test_client.connection_pool.disconnect()

    async def execute_command(self, *args: str) -> Any:
        """Execute a Redis command and return the response."""
        if not args:
            raise ValueError("No command specified")
        if self._test_client is None:
            raise RuntimeError("Test client not initialized")

        # Convert all arguments to strings as expected by the RESP protocol
        str_args = [str(arg) for arg in args]
        return await self._test_client.execute_command(*str_args)
