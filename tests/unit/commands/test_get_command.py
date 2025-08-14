"""Unit tests for the Redis GET command."""
from unittest.mock import MagicMock

import pytest

from app.commands.string.get_command import GetCommand
from app.store import Store


class TestGetCommand:
    """Test cases for the GetCommand class."""

    @pytest.fixture
    def command(self):
        """Create a GetCommand instance for testing."""
        return GetCommand()

    @pytest.fixture
    def mock_store(self):
        """Create a mock store instance with a get_key method."""
        store = MagicMock(spec=Store)
        store.get_key.return_value = None
        return store

    @pytest.mark.asyncio
    async def test_name_returns_uppercase_get(self, command):
        """Test that the name property returns 'GET' in uppercase."""
        assert command.name == "GET"

    @pytest.mark.asyncio
    async def test_execute_returns_value_for_existing_key(self, command, mock_store):
        """Test that execute returns the value for an existing key."""
        # Setup mock to return a value for the key
        mock_store.get_key.return_value = "test_value"

        result = await command.execute("test_key", store=mock_store)

        mock_store.get_key.assert_called_once_with("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_execute_returns_none_for_non_existing_key(self, command, mock_store):
        """Test that execute returns None for a non-existing key."""
        # Setup mock to return None (key doesn't exist)
        mock_store.get_key.return_value = None

        result = await command.execute("non_existing_key", store=mock_store)

        mock_store.get_key.assert_called_once_with("non_existing_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_raises_error_without_store(self, command):
        """Test that execute raises ValueError when store is not provided."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("key")
        assert "Store instance is required for GET command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_raises_error_with_wrong_number_of_arguments(
        self, command, mock_store
    ):
        """Test that execute raises ValueError with wrong number of arguments."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("key1", "key2", store=mock_store)
        assert "wrong number of arguments for 'get' command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_handles_non_string_key(self, command, mock_store):
        """Test that execute converts non-string key to string."""
        # Setup mock to return a value
        mock_store.get_key.return_value = "test_value"

        result = await command.execute(123, store=mock_store)

        # Should convert the integer key to string
        mock_store.get_key.assert_called_once_with("123")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_execute_handles_whitespace_in_key(self, command, mock_store):
        """Test that execute handles keys with whitespace."""
        # Setup mock to return a value
        mock_store.get_key.return_value = "test_value"

        result = await command.execute("my key", store=mock_store)

        mock_store.get_key.assert_called_once_with("my key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_execute_handles_empty_key(self, command, mock_store):
        """Test that execute handles empty key string."""
        # Setup mock to return a value for empty key
        mock_store.get_key.return_value = "empty_key_value"

        result = await command.execute("", store=mock_store)

        mock_store.get_key.assert_called_once_with("")
        assert result == "empty_key_value"
