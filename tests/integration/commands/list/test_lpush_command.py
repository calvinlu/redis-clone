"""Integration tests for the LPUSH command."""
import pytest

from tests.integration.commands.base_command_test import BaseCommandTest


class TestLPushCommand(BaseCommandTest):
    """Integration tests for the LPUSH command."""

    @pytest.mark.asyncio
    async def test_lpush_to_new_list(self, dispatcher):
        """Test LPUSH creates a new list and returns its length."""
        result = await self.execute_command(
            dispatcher, "LPUSH", "mylist", "value1", "value2"
        )
        assert result == 2

    @pytest.mark.asyncio
    async def test_lpush_to_existing_list(self, dispatcher):
        """Test LPUSH prepends to an existing list and returns the new length."""
        # First push
        await self.execute_command(dispatcher, "LPUSH", "mylist", "value1")
        # Second push with multiple values
        result = await self.execute_command(
            dispatcher, "LPUSH", "mylist", "value2", "value3"
        )
        assert result == 3

    @pytest.mark.asyncio
    async def test_lpush_verifies_order(self, dispatcher):
        """Test LPUSH maintains correct order of elements (last value becomes head)."""
        await self.execute_command(dispatcher, "LPUSH", "mylist", "value1", "value2")
        result = await self.execute_command(dispatcher, "LRANGE", "mylist", "0", "-1")
        assert result == ["value2", "value1"]  # Last pushed value is first

    @pytest.mark.asyncio
    async def test_lpush_wrong_type(self, dispatcher):
        """Test LPUSH returns an error when used against a non-list key."""
        # Create a string key
        await self.execute_command(dispatcher, "SET", "mystring", "value")
        # Try to LPUSH to a string key
        with pytest.raises(TypeError) as exc_info:
            await self.execute_command(dispatcher, "LPUSH", "mystring", "value2")
        assert "WRONGTYPE" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_lpush_multiple_values(self, dispatcher):
        """Test LPUSH with multiple values maintains correct order."""
        result = await self.execute_command(
            dispatcher, "LPUSH", "mylist", "value1", "value2", "value3"
        )
        assert result == 3
        # Verify the order is value3, value2, value1
        lrange = await self.execute_command(dispatcher, "LRANGE", "mylist", "0", "-1")
        assert lrange == ["value3", "value2", "value1"]
