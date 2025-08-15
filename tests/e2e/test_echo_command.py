"""End-to-end tests for the ECHO command."""
import pytest
from redis.exceptions import ResponseError

from tests.e2e.base_e2e_test import BaseE2ETest


class TestEchoE2E(BaseE2ETest):
    """End-to-end tests for the ECHO command."""

    @pytest.mark.asyncio
    async def test_echo_basic(self):
        """Test basic ECHO command."""
        test_message = "Hello, Redis!"
        result = await self.execute_command("ECHO", test_message)
        assert result == test_message, f"Expected {test_message!r}, got {result!r}"

    @pytest.mark.asyncio
    async def test_echo_with_special_characters(self):
        """Test ECHO with special characters."""
        test_message = "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        result = await self.execute_command("ECHO", test_message)
        assert result == test_message, f"Expected {test_message!r}, got {result!r}"

    @pytest.mark.asyncio
    async def test_echo_empty_string(self):
        """Test ECHO with an empty string."""
        result = await self.execute_command("ECHO", "")
        assert result == "", f"Expected empty string, got {result!r}"

    @pytest.mark.asyncio
    async def test_echo_invalid_arguments(self):
        """Test ECHO with invalid arguments."""
        # Test with no arguments
        with pytest.raises(ResponseError, match="wrong number of arguments"):
            await self.execute_command("ECHO")

        # Test with too many arguments (ECHO only accepts 1 argument)
        with pytest.raises(ResponseError, match="wrong number of arguments"):
            await self.execute_command("ECHO", "message1", "message2")
