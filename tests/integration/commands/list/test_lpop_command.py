"""Integration tests for the LPOP command."""
import pytest

from tests.integration.commands.base_command_test import BaseCommandTest


class TestLPopCommand(BaseCommandTest):
    """Integration tests for the LPOP command."""

    @pytest.mark.asyncio
    async def test_lpop_from_empty_list(self, dispatcher):
        """Test LPOP on non-existent key returns -1."""
        result = await self.execute_command(dispatcher, "LPOP", "nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_lpop_removes_and_returns_first_element(self, dispatcher):
        """Test LPOP removes and returns the first element."""
        # First create a list
        await self.execute_command(dispatcher, "RPUSH", "mylist", "a", "b", "c")

        # Test LPOP
        result = await self.execute_command(dispatcher, "LPOP", "mylist")
        assert result == "a"

        # Verify the list was modified
        remaining = await self.execute_command(
            dispatcher, "LRANGE", "mylist", "0", "-1"
        )
        assert remaining == ["b", "c"]

    @pytest.mark.asyncio
    async def test_lpop_until_empty(self, dispatcher):
        """Test LPOP until list is empty."""
        # First create a list
        await self.execute_command(dispatcher, "RPUSH", "mylist", "a", "b", "c")

        # Pop all elements
        assert await self.execute_command(dispatcher, "LPOP", "mylist") == "a"
        assert await self.execute_command(dispatcher, "LPOP", "mylist") == "b"
        assert await self.execute_command(dispatcher, "LPOP", "mylist") == "c"

        # List should now be empty
        assert await self.execute_command(dispatcher, "LPOP", "mylist") == None
        assert await self.execute_command(dispatcher, "LLEN", "mylist") == 0

    @pytest.mark.asyncio
    async def test_lpop_with_wrong_type(self, dispatcher):
        """Test LPOP on a non-list key raises an error."""
        # Create a string key
        await self.execute_command(dispatcher, "SET", "mystring", "hello")

        # Try to LPOP on string should raise error
        with pytest.raises(TypeError, match="WRONGTYPE"):
            await self.execute_command(dispatcher, "LPOP", "mystring")

    @pytest.mark.asyncio
    async def test_lpop_with_wrong_number_of_arguments(self, dispatcher):
        """Test LPOP with wrong number of arguments raises an error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            await self.execute_command(dispatcher, "LPOP")

        with pytest.raises(
            ValueError, match="number of elements to lpop should be int"
        ):
            await self.execute_command(dispatcher, "LPOP", "key1", "key2")
