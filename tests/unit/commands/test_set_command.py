"""Unit tests for the Redis SET command."""
from unittest.mock import MagicMock

import pytest

from app.commands.string.set_command import SetCommand
from app.store import Store


class TestSetCommand:
    """Test cases for the SetCommand class."""

    @pytest.fixture
    def command(self):
        """Create a SetCommand instance for testing."""
        return SetCommand()

    @pytest.fixture
    def mock_store(self):
        """Create a mock store instance."""
        return MagicMock(spec=Store)

    @pytest.mark.asyncio
    async def test_name_returns_uppercase_set(self, command):
        """Test that the name property returns 'SET' in uppercase."""
        assert command.name == "SET"

    @pytest.mark.asyncio
    async def test_execute_sets_key_value(self, command, mock_store):
        """Test that execute sets a key-value pair in the store."""
        result = await command.execute("test_key", "test_value", store=mock_store)

        mock_store.set_key.assert_called_once_with("test_key", "test_value", ttl=None)
        assert result == "OK"

    @pytest.mark.asyncio
    async def test_execute_sets_key_with_ttl(self, command, mock_store):
        """Test that execute sets a key with TTL when PX argument is provided."""
        result = await command.execute(
            "test_key", "test_value", "PX", "5000", store=mock_store
        )

        mock_store.set_key.assert_called_once_with("test_key", "test_value", ttl=5000)
        assert result == "OK"

    @pytest.mark.asyncio
    async def test_execute_raises_error_without_store(self, command):
        """Test that execute raises ValueError when store is not provided."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("key", "value")
        assert "Store instance is required for SET command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_raises_error_with_insufficient_arguments(
        self, command, mock_store
    ):
        """Test that execute raises ValueError with insufficient arguments."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("key", store=mock_store)
        assert "wrong number of arguments for 'set' command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_raises_error_with_invalid_ttl_format(
        self, command, mock_store
    ):
        """Test that execute raises ValueError with invalid TTL format."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute(
                "key", "value", "PX", "not_a_number", store=mock_store
            )
        assert "invalid expire time in 'set' command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_raises_error_with_negative_ttl(self, command, mock_store):
        """Test that execute raises ValueError with negative TTL."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("key", "value", "PX", "-1000", store=mock_store)
        assert "invalid expire time in 'set' command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_raises_error_with_invalid_arguments_after_px(
        self, command, mock_store
    ):
        """Test that execute raises ValueError with invalid arguments after PX."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("key", "value", "PX", store=mock_store)
        assert "syntax error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_handles_non_string_arguments(self, command, mock_store):
        """Test that execute converts non-string key and value to strings."""
        result = await command.execute(123, 456, store=mock_store)

        mock_store.set_key.assert_called_once_with("123", "456", ttl=None)
        assert result == "OK"

    @pytest.mark.asyncio
    async def test_execute_handles_whitespace_in_key_or_value(
        self, command, mock_store
    ):
        """Test that execute handles keys and values with whitespace."""
        result = await command.execute("my key", "my value", store=mock_store)

        mock_store.set_key.assert_called_once_with("my key", "my value", ttl=None)
        assert result == "OK"
