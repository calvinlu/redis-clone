"""End-to-end tests for the LPOP command."""
import pytest
from redis.exceptions import ResponseError

from tests.e2e.base_e2e_test import BaseE2ETest


class TestLPOPE2E(BaseE2ETest):
    """End-to-end tests for the LPOP command."""

    @pytest.mark.asyncio
    async def test_lpop_basic_operations(self):
        """Test basic LPOP operations."""
        # Test LPOP on non-existent key returns None (Redis returns nil)
        result = await self.execute_command("LPOP", "nonexistent")
        assert result is None, f"Expected None for non-existent key, got {result!r}"

        # Create a list
        await self.execute_command("RPUSH", "mylist", "one", "two", "three")

        # Test LPOP returns first element
        result = await self.execute_command("LPOP", "mylist")
        assert result == "one", f"Expected 'one', got {result!r}"

        # Verify the element was removed
        result = await self.execute_command("LRANGE", "mylist", "0", "-1")
        assert result == ["two", "three"], f"Expected ['two', 'three'], got {result!r}"

    @pytest.mark.asyncio
    async def test_lpop_until_empty(self):
        """Test LPOP until list is empty."""
        # Create a list
        await self.execute_command("RPUSH", "mylist", "a", "b", "c")

        # Pop all elements
        assert await self.execute_command("LPOP", "mylist") == "a"
        assert await self.execute_command("LPOP", "mylist") == "b"
        assert await self.execute_command("LPOP", "mylist") == "c"

        # List should now be empty
        assert await self.execute_command("LPOP", "mylist") is None
        assert await self.execute_command("LLEN", "mylist") == 0

    @pytest.mark.asyncio
    async def test_lpop_with_large_number_of_elements(self):
        """Test LPOP with a large number of elements."""
        # Create a large list
        num_of_elements = 100
        values = [f"value{i}" for i in range(num_of_elements)]
        await self.execute_command("RPUSH", "biglist", *values)

        # Pop elements and verify order
        for i in range(num_of_elements):
            result = await self.execute_command("LPOP", "biglist")
            assert result == f"value{i}", f"Expected 'value{i}', got {result!r}"

        # List should be empty now
        assert await self.execute_command("LPOP", "biglist") is None

    @pytest.mark.asyncio
    async def test_lpop_with_wrong_type(self):
        """Test LPOP on a non-list key raises WRONGTYPE error."""
        # Create a string key
        await self.execute_command("SET", "mystring", "hello")

        # Try to LPOP on string should raise error
        with pytest.raises(ResponseError, match="WRONGTYPE"):
            await self.execute_command("LPOP", "mystring")

    @pytest.mark.asyncio
    async def test_lpop_with_empty_string(self):
        """Test LPOP with empty string as list element."""
        await self.execute_command("RPUSH", "emptylist", "")
        result = await self.execute_command("LPOP", "emptylist")
        assert result == "", f"Expected empty string, got {result!r}"

        # List should be empty now
        assert await self.execute_command("LLEN", "emptylist") == 0

    @pytest.mark.asyncio
    async def test_lpop_wrong_number_of_arguments(self):
        """Test LPOP with wrong number of arguments."""
        # No arguments
        with pytest.raises(ResponseError, match="wrong number of arguments"):
            await self.execute_command("LPOP")

        # Too many arguments
        with pytest.raises(ResponseError, match="wrong number of arguments"):
            await self.execute_command("LPOP", "key1", "key2")
