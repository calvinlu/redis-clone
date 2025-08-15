"""Unit tests for the LLEN command."""
from unittest.mock import MagicMock, patch

import pytest

from app.commands.list.llen_command import LLenCommand


class TestLLenCommand:
    """Test LLEN command functionality."""

    @pytest.fixture
    def command(self):
        """Return a new LLenCommand instance for each test."""
        return LLenCommand()

    def test_name_returns_uppercase(self, command):
        """Test that the command name is always uppercase."""
        assert command.name == "LLEN"

    @pytest.mark.asyncio
    async def test_execute_returns_list_length(self, command):
        """Test that execute returns the correct list length."""
        mock_store = MagicMock()
        mock_store.llen.return_value = 3

        result = await command.execute("mylist", store=mock_store)

        assert result == 3
        mock_store.llen.assert_called_once_with("mylist")

    @pytest.mark.asyncio
    async def test_execute_raises_wrong_number_of_args(self, command):
        """Test that execute raises error with wrong number of arguments."""
        with pytest.raises(
            ValueError, match="wrong number of arguments for 'rpush' command"
        ):
            await command.execute("key1", "key2", store=MagicMock())

    @pytest.mark.asyncio
    async def test_execute_raises_when_store_not_provided(self, command):
        """Test that execute raises error when store is not provided."""
        with pytest.raises(ValueError, match="store not provided in kwargs"):
            await command.execute("mylist")
