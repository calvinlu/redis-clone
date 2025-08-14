"""Integration tests for the GET command."""
import asyncio
import time

import pytest

from app.store.store import Store


class TestGetCommand:
    """Test cases for the GET command."""

    @pytest.fixture
    def command(self):
        """Get the get command instance."""
        from app.commands.get_command import command as get_command

        return get_command

    @pytest.fixture
    def store(self):
        """Create a fresh store instance for each test."""
        return Store()

    @pytest.fixture
    def store_with_data(self, store):
        """Store with some test data."""
        store.set_key("existing_key", "existing_value")
        store.set_key("expiring_key", "expiring_value", ttl=0.1)  # Will expire quickly
        return store

    @pytest.mark.asyncio
    async def test_get_existing_key(self, command, store_with_data):
        """Test getting an existing key returns its value."""
        result = await command.execute("existing_key", store=store_with_data)
        assert result == "existing_value"

    @pytest.mark.asyncio
    async def test_get_non_existing_key(self, command, store):
        """Test getting a non-existing key returns None."""
        result = await command.execute("nonexistent_key", store=store)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_expired_key_returns_none(self, command, store_with_data):
        """Test getting an expired key returns None and removes the key."""
        # Wait for the key to expire
        await asyncio.sleep(0.15)

        # The key should be expired and removed
        result = await command.execute("expiring_key", store=store_with_data)
        assert result is None
        assert "expiring_key" not in store_with_data.keys()

    @pytest.mark.asyncio
    async def test_get_with_expired_ttl_cleans_up(self, command, store):
        """Test that getting a key with expired TTL removes it from the store."""
        # Add a key with a very short TTL
        store.set_key("temp_key", "temp_value", ttl=0.1)

        # Wait for the key to expire
        await asyncio.sleep(0.15)

        # Getting the key should return None and clean it up
        result = await command.execute("temp_key", store=store)
        assert result is None
        assert "temp_key" not in store.keys()

    @pytest.mark.asyncio
    async def test_get_with_future_ttl_returns_value(self, command, store):
        """Test getting a key with future TTL returns its value."""
        # Add a key with a long TTL
        store.set_key("long_ttl_key", "long_ttl_value", ttl=3600)

        # Getting the key should return its value
        result = await command.execute("long_ttl_key", store=store)
        assert result == "long_ttl_value"

    @pytest.mark.asyncio
    async def test_get_with_invalid_arguments_raises_error(self, command, store):
        """Test that get with wrong number of arguments raises an error."""
        # No arguments
        with pytest.raises(ValueError) as exc_info:
            await command.execute(store=store)
        assert "wrong number of arguments" in str(exc_info.value).lower()

        # Too many arguments
        with pytest.raises(ValueError) as exc_info:
            await command.execute("key1", "key2", store=store)
        assert "wrong number of arguments" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_without_store_raises_error(self, command):
        """Test that get without a store raises an error."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("key")
        assert "Store instance is required for GET command" in str(exc_info.value)
