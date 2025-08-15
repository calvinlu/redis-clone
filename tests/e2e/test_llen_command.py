"""End-to-end tests for the LLEN command."""
import pytest
from redis.exceptions import ResponseError

from tests.e2e.base_e2e_test import BaseE2ETest


class TestLLenE2E(BaseE2ETest):
    """End-to-end tests for the LLEN command."""

    @pytest.mark.asyncio
    async def test_llen_basic_operations(self):
        """Test basic LLEN operations."""
        # Test LLEN on non-existent key
        result = await self.execute_command("LLEN", "nonexistent")
        print(f"LLEN nonexistent -> {result!r}")
        assert result == 0, f"Expected 0, got {result!r}"

        # Create a list
        await self.execute_command("RPUSH", "mylist", "one", "two", "three")

        # Test LLEN on existing list
        result = await self.execute_command("LLEN", "mylist")
        print(f"LLEN mylist -> {result!r}")
        assert result == 3, f"Expected 3, got {result!r}"

    @pytest.mark.asyncio
    async def test_llen_wrong_type(self):
        """Test LLEN on a key with a different type returns an error."""
        # Create a string key
        await self.execute_command("SET", "mystring", "hello")

        # Try to use LLEN on a string key
        with pytest.raises(ResponseError, match="WRONGTYPE"):
            await self.execute_command("LLEN", "mystring")

    @pytest.mark.asyncio
    async def test_llen_wrong_number_of_arguments(self):
        """Test LLEN with wrong number of arguments."""
        # Test with no arguments
        with pytest.raises(ResponseError, match="wrong number of arguments"):
            await self.execute_command("LLEN")

        # Test with too many arguments
        with pytest.raises(ResponseError, match="wrong number of arguments"):
            await self.execute_command("LLEN", "key1", "key2")
