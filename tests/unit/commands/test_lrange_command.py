"""Unit tests for the LRANGE command."""
from unittest.mock import MagicMock

import pytest

from app.commands.lrange_command import LRangeCommand


class TestLRangeCommand:
    """Test cases for the LRANGE command."""

    @pytest.fixture
    def command(self) -> LRangeCommand:
        """Return an instance of LRangeCommand for testing."""
        return LRangeCommand()

    @pytest.fixture
    def mock_store(self) -> MagicMock:
        """Return a mock store for testing."""
        store = MagicMock()
        store.lrange = MagicMock()
        return store

    @pytest.mark.asyncio
    async def test_execute_with_valid_arguments(
        self, command: LRangeCommand, mock_store: MagicMock
    ) -> None:
        """Test LRANGE with valid arguments."""
        # Setup
        mock_store.lrange.return_value = ["one", "two", "three"]

        # Execute
        result = await command.execute("mylist", "0", "-1", store=mock_store)

        # Assert
        assert result == ["one", "two", "three"]
        mock_store.lrange.assert_called_once_with("mylist", 0, -1)

    @pytest.mark.asyncio
    async def test_execute_with_insufficient_arguments_raises_error(
        self, command: LRangeCommand, mock_store: MagicMock
    ) -> None:
        """Test LRANGE with insufficient arguments raises an error."""
        # Test with no arguments
        with pytest.raises(
            ValueError, match="wrong number of arguments for 'lrange' command"
        ):
            await command.execute(store=mock_store)

        # Test with only key
        with pytest.raises(
            ValueError, match="wrong number of arguments for 'lrange' command"
        ):
            await command.execute("mylist", store=mock_store)

        # Test with only key and start
        with pytest.raises(
            ValueError, match="wrong number of arguments for 'lrange' command"
        ):
            await command.execute("mylist", "0", store=mock_store)

        # Verify store.lrange was not called
        mock_store.lrange.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_without_store_raises_error(
        self, command: LRangeCommand
    ) -> None:
        """Test LRANGE without a store raises an error."""
        with pytest.raises(ValueError, match="store not provided in kwargs"):
            await command.execute("mylist", "0", "-1")
