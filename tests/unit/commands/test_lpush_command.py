"""Unit tests for the LPUSH command."""
from unittest.mock import MagicMock

import pytest

from app.commands.list.lpush_command import LPushCommand


class TestLPushCommand:
    """Test cases for the LPUSH command."""

    @pytest.fixture
    def command(self) -> LPushCommand:
        """Return an instance of LPushCommand for testing."""
        from app.commands.list.lpush_command import command

        return command

    @pytest.fixture
    def mock_store(self) -> MagicMock:
        """Return a mock store for testing."""
        store = MagicMock()
        store.lpush = MagicMock()
        return store

    @pytest.mark.asyncio
    async def test_execute_with_valid_arguments(
        self, command: LPushCommand, mock_store: MagicMock
    ) -> None:
        """Test LPUSH with valid arguments."""
        # Setup
        mock_store.lpush.return_value = 3

        # Execute
        result = await command.execute(
            "mylist", "value1", "value2", "value3", store=mock_store
        )

        # Assert
        assert result == 3
        mock_store.lpush.assert_called_once_with("mylist", "value1", "value2", "value3")

    @pytest.mark.asyncio
    async def test_execute_with_single_value(
        self, command: LPushCommand, mock_store: MagicMock
    ) -> None:
        """Test LPUSH with a single value."""
        # Setup
        mock_store.lpush.return_value = 1

        # Execute
        result = await command.execute("mylist", "single_value", store=mock_store)

        # Assert
        assert result == 1
        mock_store.lpush.assert_called_once_with("mylist", "single_value")

    @pytest.mark.asyncio
    async def test_execute_without_store_raises_error(
        self, command: LPushCommand
    ) -> None:
        """Test LPUSH without a store raises an error."""
        with pytest.raises(ValueError, match="store not provided in kwargs"):
            await command.execute("mylist", "value1")

    @pytest.mark.asyncio
    async def test_execute_without_key_raises_error(
        self, command: LPushCommand, mock_store: MagicMock
    ) -> None:
        """Test LPUSH without a key raises an error."""
        with pytest.raises(
            ValueError, match="wrong number of arguments for 'rpush' command"
        ):
            await command.execute(store=mock_store)

    @pytest.mark.asyncio
    async def test_execute_without_values_raises_error(
        self, command: LPushCommand, mock_store: MagicMock
    ) -> None:
        """Test LPUSH without values raises an error."""
        with pytest.raises(
            ValueError, match="wrong number of arguments for 'rpush' command"
        ):
            await command.execute("mylist", store=mock_store)

    def test_command_name(self, command: LPushCommand) -> None:
        """Test the command name is correctly set."""
        assert command.name == "LPUSH"
