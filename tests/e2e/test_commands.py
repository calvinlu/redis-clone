"""End-to-end tests for Redis command responses."""
import asyncio

import pytest

from tests.e2e.base_e2e_test import BaseE2ETest


class TestCommandResponses(BaseE2ETest):
    """Test that commands return properly formatted RESP2 responses."""

    @pytest.mark.asyncio
    async def test_ping_command(self):
        """Test that PING returns the correct response."""
        response = await self.execute_command("PING")
        assert response == True

    @pytest.mark.asyncio
    async def test_get_set_commands(self):
        """Test basic GET/SET command flow."""
        # Test SET
        response = await self.execute_command("SET", "mykey", "myvalue")
        assert response == True

        # Test GET
        response = await self.execute_command("GET", "mykey")
        assert response == "myvalue"

        # Test GET non-existent key
        response = await self.execute_command("GET", "nonexistent")
        assert response is None

    @pytest.mark.asyncio
    async def test_expiration(self):
        """Test that keys with TTL expire correctly."""
        # Set key with short TTL (100ms)
        response = await self.execute_command(
            "SET", "temp_key", "temp_value", "PX", "100"
        )
        assert response == True

        # Should still exist
        response = await self.execute_command("GET", "temp_key")
        assert response == "temp_value"

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Should be expired (returns None)
        response = await self.execute_command("GET", "temp_key")
        assert response is None

    @pytest.mark.asyncio
    async def test_invalid_command(self):
        """Test that invalid commands return an error."""
        with pytest.raises(Exception, match="unknown command"):
            await self.execute_command("NOSUCHCOMMAND")

    @pytest.mark.asyncio
    async def test_wrong_number_of_arguments(self):
        """Test that commands with wrong number of arguments return an error."""
        with pytest.raises(Exception, match="wrong number of arguments"):
            await self.execute_command("GET")


# This allows running the tests with:
# python -m pytest tests/integration/test_command_responses.py -v
if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
