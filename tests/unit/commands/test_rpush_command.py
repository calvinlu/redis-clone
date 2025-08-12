"""Unit tests for the RPUSH command."""
from unittest.mock import MagicMock

import pytest

from app.commands.rpush_command import RPushCommand


class TestRPushCommand:
    """Test cases for the RPUSH command."""

    @pytest.fixture
    def command(self) -> RPushCommand:
        """Return an instance of RPushCommand for testing."""
        return RPushCommand()

    @pytest.fixture
    def mock_store(self) -> MagicMock:
        """Return a mock store for testing."""
        store = MagicMock()
        store.rpush = MagicMock()
        return store

    @pytest.mark.asyncio
    async def test_execute_with_valid_arguments(
        self, command: RPushCommand, mock_store: MagicMock
    ) -> None:
        """Test RPUSH with valid arguments."""
        # Setup
        mock_store.rpush.return_value = 3

        # Execute
        result = await command.execute(
            "mylist", "value1", "value2", "value3", store=mock_store
        )

        # Assert
        assert result == 3
        mock_store.rpush.assert_called_once_with("mylist", "value1", "value2", "value3")

    @pytest.mark.asyncio
    async def test_execute_with_single_value(
        self, command: RPushCommand, mock_store: MagicMock
    ) -> None:
        """Test RPUSH with a single value."""
        # Setup
        mock_store.rpush.return_value = 1

        # Execute
        result = await command.execute("mylist", "single_value", store=mock_store)

        # Assert
        assert result == 1
        mock_store.rpush.assert_called_once_with("mylist", "single_value")

    @pytest.mark.asyncio
    async def test_execute_without_store_raises_error(
        self, command: RPushCommand
    ) -> None:
        """Test RPUSH without a store raises an error."""
        with pytest.raises(ValueError, match="store not provided in kwargs"):
            await command.execute("mylist", "value1")

    @pytest.mark.asyncio
    async def test_execute_without_key_raises_error(
        self, command: RPushCommand, mock_store: MagicMock
    ) -> None:
        """Test RPUSH without a key raises an error."""
        with pytest.raises(
            ValueError, match="wrong number of arguments for 'rpush' command"
        ):
            await command.execute(store=mock_store)

    @pytest.mark.asyncio
    async def test_execute_without_values_raises_error(
        self, command: RPushCommand, mock_store: MagicMock
    ) -> None:
        """Test RPUSH without values raises an error."""
        with pytest.raises(
            ValueError, match="wrong number of arguments for 'rpush' command"
        ):
            await command.execute("mylist", store=mock_store)

    def test_command_name(self, command: RPushCommand) -> None:
        """Test the command name is correctly set."""
        assert command.name == "RPUSH"
