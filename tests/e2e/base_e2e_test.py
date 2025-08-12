"""Base class for end-to-end tests."""
import os
import socket
import subprocess
import time
from typing import Optional

import pytest

# Get the server port from environment or use default
TEST_PORT = int(os.environ.get("TEST_PORT", "6379"))
SERVER_HOST = os.environ.get("SERVER_HOST", "localhost")


class RedisTestClient:
    """A simple Redis client using raw sockets for testing."""

    def __init__(self, host: str = SERVER_HOST, port: int = TEST_PORT):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def send_command(self, *args: str) -> str:
        """Send a command to the Redis server using RESP protocol."""
        command = f"*{len(args)}\r\n"
        for arg in args:
            command += f"${len(str(arg).encode('utf-8'))}\r\n{arg}\r\n"
        self.socket.sendall(command.encode("utf-8"))
        return self._read_response()

    def _read_response(self) -> str:
        """Read and parse the server response."""
        response = self.socket.recv(1024).decode("utf-8")
        return response.strip()

    def close(self):
        """Close the connection."""
        self.socket.close()


class BaseE2ETest:
    """Base class for end-to-end tests that need a running Redis server."""

    _server_process: Optional[subprocess.Popen] = None
    _test_client: Optional[RedisTestClient] = None

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
    def test_client(self) -> RedisTestClient:
        """Return a test client connected to the server."""
        if self._test_client is None:
            self._test_client = RedisTestClient(SERVER_HOST, TEST_PORT)
        return self._test_client

    def execute_command(self, *args: str) -> str:
        """Execute a Redis command and return the raw response."""
        if not args:
            raise ValueError("No command specified")
        if self._test_client is None:
            raise RuntimeError("Test client not initialized")
        return self._test_client.send_command(*args)
