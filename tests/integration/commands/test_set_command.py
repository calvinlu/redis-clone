"""Integration tests for the SET command."""
import asyncio

import pytest

from app.commands.set_command import command as set_command
from app.store.store import Store


class TestSetCommand:
    """Test cases for the SET command."""

    @pytest.fixture
    def command(self):
        """Get the set command instance."""

        return set_command

    @pytest.fixture
    def store(self):
        """Create a fresh store instance for each test."""
        return Store()

    @pytest.mark.asyncio
    async def test_set_key_value(self, command, store):
        """Test setting a key-value pair stores it in the store."""
        # Test
        result = await command.execute("test_key", "test_value", store=store)

        # Assert
        assert result == "OK"
        assert store.get_key("test_key") == "test_value"

    @pytest.mark.asyncio
    async def test_overwrite_existing_key(self, command, store):
        """Test that setting an existing key overwrites its value."""
        # Setup
        await command.execute("test_key", "initial_value", store=store)

        # Test
        result = await command.execute("test_key", "new_value", store=store)

        # Assert
        assert result == "OK"
        assert store.get_key("test_key") == "new_value"

    @pytest.mark.asyncio
    async def test_set_with_px_option(self, command, store):
        """Test setting a key with PX (milliseconds) option."""
        # Test
        result = await command.execute(
            "test_key", "test_value", "PX", "100", store=store
        )

        # Assert
        assert result == "OK"
        assert store.get_key("test_key") == "test_value"

        # Check that the key expires after the TTL
        await asyncio.sleep(0.2)  # Sleep longer than the TTL
        assert store.get_key("test_key") is None

    @pytest.mark.asyncio
    async def test_set_with_invalid_ttl_value(self, command, store):
        """Test that invalid TTL values raise an error."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute(
                "test_key", "value", "PX", "not_an_integer", store=store
            )
        assert "invalid expire time" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_set_with_unknown_option(self, command, store):
        """Test that unknown options raise an error."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("test_key", "value", "UNKNOWN_OPTION", store=store)
        assert "syntax error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_set_with_missing_ttl_value(self, command, store):
        """Test that missing TTL value raises an error."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("test_key", "value", "PX", store=store)
        assert "syntax error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_set_without_store_raises_error(self, command):
        """Test that set without a store raises an error."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("key", "value")
        assert "Store instance is required for SET command" in str(exc_info.value)
