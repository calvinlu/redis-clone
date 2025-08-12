"""End-to-end tests for the RPUSH command."""
import pytest

from tests.e2e.base_e2e_test import BaseE2ETest


class TestRPushE2E(BaseE2ETest):
    """End-to-end tests for the RPUSH command."""

    @pytest.mark.asyncio
    async def test_rpush_basic_operations(self):
        """Test basic RPUSH operations."""
        # Test pushing to a new list
        result = await self.execute_command("RPUSH", "mylist", "hello")
        assert result == 1

        # Test pushing multiple elements
        result = await self.execute_command("RPUSH", "mylist", "world", "!")
        assert result == 3

        # Verify the list contents
        result = await self.execute_command("LRANGE", "mylist", 0, -1)
        assert result == ["hello", "world", "!"]

    @pytest.mark.asyncio
    async def test_rpush_wrong_type(self, redis_client):
        """Test RPUSH on a key with a different type returns an error."""
        # Create a string key
        await self.execute_command("SET", "mystring", "hello")

        # Try to use RPUSH on a string key
        with pytest.raises(redis_client.ResponseError, match="WRONGTYPE"):
            await self.execute_command("RPUSH", "mystring", "value1")

    @pytest.mark.asyncio
    async def test_rpush_with_large_number_of_elements(self):
        """Test RPUSH with a large number of elements."""
        values = [f"value{i}" for i in range(1000)]
        result = await self.execute_command("RPUSH", "biglist", *values)
        assert result == 1000

        # Verify all elements were added
        result = await self.execute_command("LLEN", "biglist")
        assert result == 1000
