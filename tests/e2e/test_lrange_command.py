"""End-to-end tests for the LRANGE command."""
import pytest

from tests.e2e.base_e2e_test import BaseE2ETest


class TestLRangeCommand(BaseE2ETest):
    """Tests for the LRANGE command."""

    @pytest.mark.asyncio
    async def test_lrange_basic_operations(self):
        """Test basic LRANGE operations."""
        # First, create a list using RPUSH
        await self.execute_command("RPUSH", "mylist", "one", "two", "three")

        # Test getting the full list
        response = await self.execute_command("LRANGE", "mylist", "0", "-1")
        assert response == [
            "one",
            "two",
            "three",
        ], f"Expected full list, got {response!r}"

        # Test getting a subset of the list
        response = await self.execute_command("LRANGE", "mylist", "0", "1")
        assert response == [
            "one",
            "two",
        ], f"Expected first two elements, got {response!r}"

        # Test getting a single element
        response = await self.execute_command("LRANGE", "mylist", "0", "0")
        assert response == ["one"], f"Expected first element, got {response!r}"

        # Test with negative indices
        response = await self.execute_command("LRANGE", "mylist", "-2", "-1")
        assert response == [
            "two",
            "three",
        ], f"Expected last two elements, got {response!r}"

    @pytest.mark.asyncio
    async def test_lrange_out_of_bounds(self):
        """Test LRANGE with out-of-bounds indices."""
        # Create a list with 3 elements
        await self.execute_command("RPUSH", "lrange_bound", "a", "b", "c")

        # Start index > end index (should return empty list)
        response = await self.execute_command("LRANGE", "lrange_bound", "2", "1")
        assert response == [], f"Expected empty list, got {response!r}"

        # Start index beyond list length (should return empty list)
        response = await self.execute_command("LRANGE", "lrange_bound", "5", "10")
        assert response == [], f"Expected empty list, got {response!r}"

        # End index beyond list length (should return elements up to the end)
        response = await self.execute_command("LRANGE", "lrange_bound", "1", "10")
        assert response == ["b", "c"], f"Expected ['b', 'c'], got {response!r}"

    @pytest.mark.asyncio
    async def test_lrange_wrong_type(self):
        """Test LRANGE on a key with a different type returns an error."""
        # Create a string key
        await self.execute_command("SET", "mystring", "hello")

        # Try to use LRANGE on a string key
        with pytest.raises(Exception, match="WRONGTYPE"):
            await self.execute_command("LRANGE", "mystring", "0", "-1")

    @pytest.mark.asyncio
    async def test_lrange_nonexistent_key(self):
        """Test LRANGE on a non-existent key returns an empty list."""
        # Try to use LRANGE on a non-existent key
        response = await self.execute_command("LRANGE", "nonexistent", "0", "-1")
        assert response == [], f"Expected empty list, got {response!r}"
