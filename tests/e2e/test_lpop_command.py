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
        await self.execute_command("RPUSH", "testlist", "a", "b", "c")

        # Pop all elements
        assert await self.execute_command("LPOP", "testlist") == "a"
        assert await self.execute_command("LPOP", "testlist") == "b"
        assert await self.execute_command("LPOP", "testlist") == "c"

        # List should now be empty
        assert await self.execute_command("LPOP", "testlist") is None
        assert await self.execute_command("LLEN", "testlist") == 0

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
        with pytest.raises(
            ResponseError, match="number of elements to lpop should be int"
        ):
            await self.execute_command("LPOP", "key1", "key2")

    @pytest.mark.asyncio
    async def test_lpop_with_count_parameter(self):
        """Test LPOP with count parameter."""
        # Set up test data
        await self.execute_command(
            "RPUSH", "lpop_count", "one", "two", "three", "four", "five"
        )

        # Test LPOP with count less than list length
        result = await self.execute_command("LPOP", "lpop_count", "2")
        assert result == ["one", "two"], f"Expected ['one', 'two'], got {result!r}"

        # Verify remaining elements
        result = await self.execute_command("LRANGE", "lpop_count", "0", "-1")
        assert result == [
            "three",
            "four",
            "five",
        ], f"Expected ['three', 'four', 'five'], got {result!r}"

        # Test LPOP with count greater than remaining elements
        result = await self.execute_command("LPOP", "lpop_count", "5")
        assert result == [
            "three",
            "four",
            "five",
        ], f"Expected ['three', 'four', 'five'], got {result!r}"

        # List should now be empty
        assert await self.execute_command("LPOP", "lpop_count") is None
        assert await self.execute_command("LLEN", "lpop_count") == 0

        # Test LPOP with count 0 (should return empty list)
        await self.execute_command("RPUSH", "lpop_count", "a", "b", "c")
        result = await self.execute_command("LPOP", "lpop_count", "0")
        assert result == [], f"Expected empty list, got {result!r}"
        assert await self.execute_command("LLEN", "lpop_count") == 3  # List unchanged

        # Test LPOP with negative count (should return empty list)
        result = await self.execute_command("LPOP", "lpop_count", "-1")
        assert result == [], f"Expected empty list, got {result!r}"
        assert await self.execute_command("LLEN", "lpop_count") == 3  # List unchanged

        # Test LPOP with count on empty list
        result = await self.execute_command("LPOP", "lpop_count", "5")
        assert result == ["a", "b", "c"], f"Expected ['a', 'b', 'c'], got {result!r}"

    @pytest.mark.asyncio
    async def test_lpop_with_invalid_count(self):
        """Test LPOP with invalid count parameter."""
        # Non-integer count
        with pytest.raises(
            ResponseError, match="number of elements to lpop should be int"
        ):
            await self.execute_command("LPOP", "mylist", "not_an_integer")

        # Float count
        with pytest.raises(
            ResponseError, match="number of elements to lpop should be int"
        ):
            await self.execute_command("LPOP", "mylist", "2.5")
