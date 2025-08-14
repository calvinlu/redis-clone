"""Integration tests for the RPUSH command."""
import pytest

from tests.integration.commands.base_command_test import BaseCommandTest


class TestRPushCommand(BaseCommandTest):
    """Integration tests for the RPUSH command."""

    @pytest.mark.asyncio
    async def test_rpush_to_new_list(self, dispatcher):
        """Test RPUSH creates a new list and returns its length."""
        result = await self.execute_command(
            dispatcher, "RPUSH", "mylist", "value1", "value2"
        )
        assert result == 2

    @pytest.mark.asyncio
    async def test_rpush_to_existing_list(self, dispatcher):
        """Test RPUSH appends to an existing list and returns the new length."""
        # First push
        await self.execute_command(dispatcher, "RPUSH", "mylist", "value1")
        # Second push
        result = await self.execute_command(
            dispatcher, "RPUSH", "mylist", "value2", "value3"
        )
        assert result == 3

    @pytest.mark.asyncio
    async def test_rpush_wrong_type(self, dispatcher):
        """Test RPUSH on a key with a different type returns an error."""
        # Create a string key
        await self.execute_command(dispatcher, "SET", "mystring", "hello")

        # Try to use RPUSH on a string key - should raise a TypeError with WRONGTYPE message
        with pytest.raises(TypeError, match="WRONGTYPE"):
            await self.execute_command(dispatcher, "RPUSH", "mystring", "value1")

    @pytest.mark.asyncio
    async def test_rpush_with_large_number_of_elements(self, dispatcher):
        """Test RPUSH with a large number of elements."""
        values = [f"value{i}" for i in range(1000)]
        result = await self.execute_command(dispatcher, "RPUSH", "biglist", *values)
        assert result == 1000
