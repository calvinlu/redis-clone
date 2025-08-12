"""Base class for end-to-end tests."""
import asyncio
import os
import subprocess
import time
from typing import Any, Optional, Tuple

import pytest
import redis.asyncio as redis

# Get the server port from environment or use default
TEST_PORT = int(os.environ.get("TEST_PORT", "6379"))
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")


class BaseE2ETest:
    """Base class for end-to-end tests that need a running Redis server."""

    _server_process: Optional[subprocess.Popen] = None
    _redis_client: Optional[redis.Redis] = None

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
        if cls._server_process:
            cls._server_process.terminate()
            try:
                cls._server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls._server_process.kill()

    @pytest.fixture
    async def redis_client(self) -> redis.Redis:
        """Return a Redis client connected to the test server."""
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=SERVER_HOST,
                port=TEST_PORT,
                decode_responses=True,
                socket_timeout=5,
            )

        # Clear the database before each test
        await self._redis_client.flushdb()
        return self._redis_client

    async def execute_command(self, *args: Any) -> Any:
        """Execute a Redis command and return the result."""
        if not args:
            raise ValueError("No command specified")

        command = args[0].upper()
        args = args[1:]

        if self._redis_client is None:
            raise RuntimeError("Redis client not initialized")

        # Special handling for commands that don't follow the standard pattern
        if command == "LRANGE":
            if len(args) < 3:
                raise ValueError("LRANGE requires key, start, and end arguments")
            key, start, end = args[0], int(args[1]), int(args[2])
            return await self._redis_client.lrange(key, start, end)

        # For standard commands, use the method with the same name as the command
        if not hasattr(self._redis_client, command.lower()):
            raise ValueError(f"Unsupported command: {command}")

        method = getattr(self._redis_client, command.lower())
        return await method(*args)
