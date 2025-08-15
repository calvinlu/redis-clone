"""Integration tests for Redis commands."""
import asyncio

import pytest

from app.commands.echo_command import command as echo_command
from app.commands.string.get_command import command as get_command
from app.commands.string.set_command import command as set_command
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

        # Verify the key exists and has a TTL
        assert store.get_key("temp_key") is not None

        # Check that the key expires after the TTL
        await asyncio.sleep(1.1)  # Wait for TTL to expire
        assert store.get_key("temp_key") is None

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
        # Set up - add a key with a very short TTL (1ms)
        await set_command.execute("temp_key", "temp_value", "PX", "1", store=store)

        # Wait for the key to expire (1ms + buffer)
        await asyncio.sleep(0.1)

        # Test - should return None for expired key
        result = await get_command.execute("temp_key", store=store)

        # Assert
        assert result is None
        # Verify key is not accessible through get_key
        assert store.get_key("temp_key") is None

    @pytest.mark.asyncio
    async def test_get_with_expired_ttl_cleans_up(self, store):
        """Test that getting a key with expired TTL removes it from the store."""
        # Set up - add a key with a very short TTL (1ms)
        store.set_key("expired_key", "expired_value", ttl=1)

        # Wait for the key to expire (1ms + buffer)
        await asyncio.sleep(0.1)

        # Test - should return None for expired key
        result = await get_command.execute("expired_key", store=store)

        # Assert
        assert result is None
        # Verify key is not accessible through get_key
        assert store.get_key("expired_key") is None

    @pytest.mark.asyncio
    async def test_get_with_future_ttl_returns_value(self, store):
        """Test getting a key with future TTL returns its value."""
        # Set up - set a key with a long TTL (10 seconds)
        store.set_key("future_key", "future_value", ttl=10000)

        # Test
        result = await get_command.execute("future_key", store=store)

        # Assert
        assert result == "future_value"
        assert store.get_key("future_key") == "future_value"

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


class TestEchoCommand:
    """Test cases for the ECHO command."""

    @pytest.fixture
    def command(self):
        """Get the echo command instance."""
        return echo_command

    @pytest.mark.asyncio
    async def test_echo_returns_same_message(self, command):
        """Test that ECHO returns the same message that was sent."""
        # Test with a simple string
        result = await command.execute("Hello, World!")
        assert result == "Hello, World!"

        # Test with special characters
        result = await command.execute("!@#$%^&*()")
        assert result == "!@#$%^&*()"

    @pytest.mark.asyncio
    async def test_echo_with_multiple_arguments_uses_first(self, command):
        """Test that ECHO only uses the first argument and ignores the rest."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute("first", "second", "third")
        assert "wrong number of arguments for 'echo' command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_echo_with_empty_message(self, command):
        """Test that ECHO handles empty string as a valid message."""
        result = await command.execute("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_echo_with_whitespace(self, command):
        """Test that ECHO preserves whitespace in the message."""
        message = "  hello  world  "
        result = await command.execute(message)
        assert result == message

    @pytest.mark.asyncio
    async def test_echo_with_newlines(self, command):
        """Test that ECHO preserves newlines in the message."""
        message = "line1\nline2\nline3"
        result = await command.execute(message)
        assert result == message

    @pytest.mark.asyncio
    async def test_echo_raises_error_with_no_arguments(self, command):
        """Test that ECHO raises an error when no arguments are provided."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute()
        assert "wrong number of arguments for 'echo' command" in str(exc_info.value)
