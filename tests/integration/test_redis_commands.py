"""Integration tests for Redis commands."""
import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from app.commands.get_command import command as get_command
from app.commands.set_command import command as set_command
from app.store.store import Store


class TestSetCommand:
    """Test cases for the SET command."""

    @pytest.fixture
    def store(self):
        """Create a fresh store instance for each test."""
        return Store()

    @pytest.mark.asyncio
    async def test_set_key_value(self, store):
        """Test setting a key-value pair stores it in the store."""
        # Test
        result = await set_command.execute("test_key", "test_value", store=store)

        # Assert
        assert result == "OK"
        assert store.get_key("test_key") == "test_value"

    @pytest.mark.asyncio
    async def test_overwrite_existing_key(self, store):
        """Test that setting an existing key overwrites its value."""
        # Set up - set initial value
        await set_command.execute("test_key", "initial_value", store=store)

        # Test - overwrite the value
        result = await set_command.execute("test_key", "new_value", store=store)

        # Assert
        assert result == "OK"
        assert store.get_key("test_key") == "new_value"

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, store):
        """Test setting a key with TTL stores the expiration time."""
        # Test - set with TTL of 1000ms
        result = await set_command.execute(
            "temp_key", "temp_value", "PX", "1000", store=store
        )

        # Assert
        assert result == "OK"
        assert store.get_key("temp_key") == "temp_value"
        assert "temp_key" in store.expirations

        # Check that the expiration is set to a future time
        current_time = time.time() * 1000
        assert store.expirations["temp_key"] > current_time

    @pytest.mark.asyncio
    async def test_set_with_invalid_ttl(self, store):
        """Test setting a key with invalid TTL raises an error."""
        # Test - invalid TTL value (not a number)
        with pytest.raises(ValueError) as exc_info:
            await set_command.execute("key", "value", "PX", "not_a_number", store=store)
        assert "invalid expire time" in str(exc_info.value).lower()

        # Test - negative TTL value
        with pytest.raises(ValueError) as exc_info:
            await set_command.execute("key", "value", "PX", "-1000", store=store)
        assert "invalid expire time" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_set_with_missing_arguments(self, store):
        """Test that set with missing arguments raises an error."""
        # Test - missing key and value
        with pytest.raises(ValueError) as exc_info:
            await set_command.execute(store=store)
        assert "wrong number of arguments" in str(exc_info.value)

        # Test - missing value
        with pytest.raises(ValueError) as exc_info:
            await set_command.execute("key", store=store)
        assert "wrong number of arguments" in str(exc_info.value)

        # Test - missing TTL value (should raise syntax error)
        with pytest.raises(ValueError) as exc_info:
            await set_command.execute("key", "value", "PX", store=store)
        assert "syntax error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_set_without_store_raises_error(self):
        """Test that set without a store raises an error."""
        with pytest.raises(ValueError) as exc_info:
            await set_command.execute("key", "value")
        assert "Store instance is required for SET command" in str(exc_info.value)


class TestGetCommand:
    """Test cases for the GET command."""

    @pytest.fixture
    def store(self):
        """Create a fresh store instance for each test."""
        return Store()

    @pytest.mark.asyncio
    async def test_get_existing_key(self, store):
        """Test getting an existing key returns its value."""
        # Set up
        await set_command.execute("test_key", "test_value", store=store)

        # Test
        result = await get_command.execute("test_key", store=store)

        # Assert
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_get_non_existing_key(self, store):
        """Test getting a non-existing key returns None."""
        # Test
        result = await get_command.execute("non_existing_key", store=store)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_expired_key_returns_none(self, store):
        """Test getting an expired key returns None and removes the key."""
        # Set up - set a key with a very short TTL (1ms)
        store.set_key("temp_key", "temp_value", ttl=1)

        # Wait for the key to expire
        await asyncio.sleep(0.01)  # 10ms should be enough for the key to expire

        # Test
        result = await get_command.execute("temp_key", store=store)

        # Assert
        assert result is None
        assert "temp_key" not in store.store
        assert "temp_key" not in store.expirations

    @pytest.mark.asyncio
    async def test_get_with_expired_ttl_cleans_up(self, store):
        """Test that getting a key with expired TTL removes it from both stores."""
        # Set up - manually add a key with expired TTL
        store.store["expired_key"] = "expired_value"
        store.expirations["expired_key"] = (
            time.time() * 1000
        ) - 1000  # 1 second in the past

        # Test
        result = await get_command.execute("expired_key", store=store)

        # Assert
        assert result is None
        assert "expired_key" not in store.store
        assert "expired_key" not in store.expirations

    @pytest.mark.asyncio
    async def test_get_with_future_ttl_returns_value(self, store):
        """Test getting a key with future TTL returns its value."""
        # Set up - set a key with a long TTL (10 seconds)
        store.set_key("future_key", "future_value", ttl=10000)

        # Test
        result = await get_command.execute("future_key", store=store)

        # Assert
        assert result == "future_value"
        assert "future_key" in store.store
        assert "future_key" in store.expirations

    @pytest.mark.asyncio
    async def test_get_with_invalid_arguments_raises_error(self, store):
        """Test that get with wrong number of arguments raises an error."""
        with pytest.raises(ValueError) as exc_info:
            await get_command.execute("key1", "key2", store=store)
        assert "wrong number of arguments for 'get' command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_without_store_raises_error(self):
        """Test that get without a store raises an error."""
        with pytest.raises(ValueError) as exc_info:
            await get_command.execute("key")
        assert "Store instance is required for GET command" in str(exc_info.value)
