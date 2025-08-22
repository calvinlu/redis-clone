"""Unit tests for the Redis TYPE command."""
from unittest.mock import MagicMock

import pytest

from app.commands.type_command import TypeCommand
from app.store import Store


class TestTypeCommand:
    """Test cases for the TypeCommand class."""

    @pytest.fixture
    def command(self):
        """Create a TypeCommand instance for testing."""
        return TypeCommand()

    @pytest.fixture
    def mock_store(self):
        """Create a mock store instance with a type method."""
        store = MagicMock(spec=Store)
        store.type.return_value = "none"
        return store

    @pytest.mark.asyncio
    async def test_name_returns_uppercase_type(self, command):
        """Test that the name property returns 'TYPE' in uppercase."""
        assert command.name == "TYPE"

    @pytest.mark.asyncio
    async def test_execute_returns_type_for_key(self, command, mock_store):
        """Test that execute returns the type for an existing key."""
        # Setup mock to return a type for the key
        mock_store.type.return_value = "string"

        result = await command.execute("test_key", store=mock_store)

        mock_store.type.assert_called_once_with("test_key")
        assert result == "string"

    @pytest.mark.asyncio
    async def test_execute_returns_none_for_non_existing_key(self, command, mock_store):
        """Test that execute returns 'none' for a non-existing key."""
        # Setup mock to return 'none' for non-existing key
        mock_store.type.return_value = "none"

        result = await command.execute("non_existing_key", store=mock_store)

        mock_store.type.assert_called_once_with("non_existing_key")
        assert result == "none"

    @pytest.mark.asyncio
    async def test_execute_raises_error_with_wrong_number_of_arguments(
        self, command, mock_store
    ):
        """Test that execute raises an error with wrong number of arguments."""
        with pytest.raises(
            ValueError, match="ERR wrong number of arguments for 'type' command"
        ):
            await command.execute("key1", "key2", store=mock_store)

        with pytest.raises(
            ValueError, match="ERR wrong number of arguments for 'type' command"
        ):
            await command.execute(store=mock_store)  # No key provided
