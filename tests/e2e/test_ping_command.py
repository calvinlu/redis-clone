"""End-to-end tests for the PING command."""
import pytest
from redis.exceptions import ResponseError

from tests.e2e.base_e2e_test import BaseE2ETest


class TestPingE2E(BaseE2ETest):
    """End-to-end tests for the PING command."""

    @pytest.mark.asyncio
    async def test_ping_basic(self):
        """Test basic PING command."""
        result = await self.execute_command("PING")
        assert result == True

    @pytest.mark.asyncio
    async def test_ping_with_message(self):
        """Test PING command with a custom message."""
        test_message = "Hello, Redis!"
        result = await self.execute_command("PING", test_message)
        assert result == True
