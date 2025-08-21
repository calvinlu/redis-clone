"""Integration tests for the GET command."""
import pytest

from app.commands.string.get_command import command as get_command
from app.store.store import Store


class TestGetCommand:
    """Test cases for the GET command."""

    @pytest.fixture
    def command(self):
        """Get the get command instance."""

        return get_command

    @pytest.fixture
    def mock_time(self):
        """Create a mock time function that we can control."""
        # Start at 1,000,000,000 milliseconds since epoch
        current_time = 1_000_000_000.0

        def get_time():
            return current_time

        def set_time(new_time):
            nonlocal current_time
            current_time = new_time

        get_time.set = set_time
        # Advance time by the specified number of milliseconds
        get_time.advance = lambda ms: set_time(current_time + ms)
        return get_time

    @pytest.fixture
    def store(self, mock_time):
        """Create a fresh store instance for each test with controlled time."""
        store = Store()
        store.set_time_function(mock_time)
        return store

    @pytest.fixture
    def store_with_data(self, store, mock_time):
        """Store with some test data and controlled time."""
        # Set initial time to known value
        mock_time.set(1_000_000.0)
        store.set_key("existing_key", "existing_value")
        store.set_key("expiring_key", "expiring_value", ttl=1000)  # 1000ms TTL
        return store

    @pytest.mark.asyncio
    async def test_get_expired_key_returns_none(
        self, command, store_with_data, mock_time
    ):
        """Test getting an expired key returns None and is treated as non-existent."""
        # First verify the key exists and has a value
        result = await command.execute("expiring_key", store=store_with_data)
        assert result == "expiring_value"

        # Fast forward time to after TTL (1001ms later)
        mock_time.advance(1001)  # 1001ms later

        # The key should now be expired and return None
        result = await command.execute("expiring_key", store=store_with_data)
        assert result is None

        # Verify the key is treated as non-existent by checking a subsequent GET
        result = await command.execute("expiring_key", store=store_with_data)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_expired_ttl_cleans_up(self, command, store, mock_time):
        """Test that getting a key with expired TTL returns None and treats it as non-existent."""
        # Set initial time to known value
        mock_time.set(1_000_000.0)

        # Add a key with a TTL
        store.set_key("temp_key", "temp_value", ttl=500)  # 500ms TTL

        # Verify the key exists initially
        result = await command.execute("temp_key", store=store)
        assert result == "temp_value"

        # Fast forward time to after TTL (501ms later)
        mock_time.advance(501)

        # Getting the key should return None and clean it up
        result = await command.execute("temp_key", store=store)
        assert result is None

        # Verify the key is treated as non-existent in subsequent gets
        result = await command.execute("temp_key", store=store)
        assert result is None

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
    async def test_get_with_future_ttl_returns_value(self, command, store, mock_time):
        """Test getting a key with future TTL returns its value."""
        # Set initial time to known value
        mock_time.set(1_000_000.0)

        # Add a key with a long TTL
        store.set_key("long_ttl_key", "long_ttl_value", ttl=3600000)  # 1 hour TTL

        # Fast forward time to just before TTL (59 minutes later)
        mock_time.advance(59 * 60 * 1000)  # 59 minutes in ms

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
            await command.execute("some_key")
        assert "store instance is required" in str(exc_info.value).lower()
