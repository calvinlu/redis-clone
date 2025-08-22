"""Unit tests for the Redis XADD command."""
from unittest.mock import MagicMock, patch

import pytest

from app.commands.stream.xadd_command import XAddCommand
from app.store import Store


class TestXAddCommand:
    """Test cases for the XAddCommand class."""

    @pytest.fixture
    def command(self):
        """Create an XAddCommand instance for testing."""
        return XAddCommand()

    @pytest.fixture
    def mock_store(self):
        """Create a mock store instance with stream operations."""
        store = MagicMock(spec=Store)
        store.xadd.return_value = "0-1"
        return store

    @pytest.mark.asyncio
    async def test_name_returns_uppercase_xadd(self, command):
        """Test that the name property returns 'XADD' in uppercase."""
        assert command.name == "XADD"

    @pytest.mark.asyncio
    async def test_execute_creates_new_stream(self, command, mock_store):
        """Test that execute creates a new stream when it doesn't exist."""
        result = await command.execute(
            "mystream", "0-1", "temperature", "36", store=mock_store
        )

        mock_store.xadd.assert_called_once_with("mystream", "0-1", "temperature", "36")
        assert result == "0-1"

    @pytest.mark.asyncio
    async def test_execute_raises_error_with_odd_arguments(self, command, mock_store):
        """Test that execute raises an error with odd number of field-value pairs."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            await command.execute("mystream", "0-1", "temperature", store=mock_store)

    @pytest.mark.asyncio
    async def test_execute_returns_entry_id(self, command, mock_store):
        """Test that execute returns the entry ID."""
        mock_store.xadd.return_value = "1526919030474-0"
        result = await command.execute(
            "mystream", "1526919030474-0", "temperature", "36", store=mock_store
        )
        assert result == "1526919030474-0"

    @pytest.mark.asyncio
    async def test_execute_handles_multiple_field_value_pairs(
        self, command, mock_store
    ):
        """Test that execute handles multiple field-value pairs."""
        result = await command.execute(
            "mystream",
            "0-1",
            "temperature",
            "36",
            "humidity",
            "95",
            "pressure",
            "1013",
            store=mock_store,
        )

        mock_store.xadd.assert_called_once_with(
            "mystream", "0-1", "temperature", "36", "humidity", "95", "pressure", "1013"
        )
        assert result == "0-1"
