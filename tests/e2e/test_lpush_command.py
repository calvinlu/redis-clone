"""End-to-end tests for the LPUSH command."""
import pytest
from redis.exceptions import ResponseError

from tests.e2e.base_e2e_test import BaseE2ETest


class TestLPushE2E(BaseE2ETest):
    """End-to-end tests for the LPUSH command."""

    @pytest.mark.asyncio
    async def test_lpush_basic_operations(self):
        """Test basic LPUSH operations."""
        # Test pushing to a new list
        result = await self.execute_command("LPUSH", "mylist", "world")
        print(f"LPUSH mylist world -> {result!r}")
        assert result == 1, f"Expected 1, got {result!r}"

        # Test pushing multiple elements (they should be inserted in reverse order)
        result = await self.execute_command("LPUSH", "mylist", "hello", "!")
        print(f"LPUSH mylist hello ! -> {result!r}")
        assert result == 3, f"Expected 3, got {result!r}"

        # Verify the list contents using LRANGE
        result = await self.execute_command("LRANGE", "mylist", "0", "-1")
        assert result == [
            "!",
            "hello",
            "world",
        ], f"Unexpected list contents: {result!r}"

    @pytest.mark.asyncio
    async def test_lpush_wrong_type(self):
        """Test LPUSH on a key with a different type returns an error."""
        # Create a string key
        await self.execute_command("SET", "mystring", "hello")

        # Try to use LPUSH on a string key
        with pytest.raises(ResponseError, match="WRONGTYPE"):
            await self.execute_command("LPUSH", "mystring", "value1")

    @pytest.mark.asyncio
    async def test_lpush_with_large_number_of_elements(self):
        """Test LPUSH with a large number of elements."""
        values = [f"value{i}" for i in range(1000)]
        result = await self.execute_command("LPUSH", "biglist", *values)
        assert result == 1000, f"Expected 1000, got {result}"

        result = await self.execute_command("LLEN", "biglist")
        assert result == 1000, f"Expected list length 1000, got {result}"

    @pytest.mark.asyncio
    async def test_lpush_empty_value(self):
        """Test LPUSH with empty string as value."""
        result = await self.execute_command("LPUSH", "emptylist", "")
        assert result == 1, f"Expected 1, got {result!r}"

    @pytest.mark.asyncio
    async def test_lpush_multiple_empty_values(self):
        """Test LPUSH with multiple empty strings."""
        result = await self.execute_command("LPUSH", "empties", "", "", "")
        assert result == 3, f"Expected 3, got {result!r}"

        # Verify the list contains three empty strings
        result = await self.execute_command("LLEN", "empties")
        assert result == 3, f"Expected 3, got {result!r}"
