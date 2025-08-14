"""Integration tests for the LRANGE command."""
import pytest

from app.store.store import Store


class TestLRangeCommand:
    """Test cases for the LRANGE command."""

    @pytest.fixture
    def command(self):
        """Get the lrange command instance."""
        from app.commands.lrange_command import command as lrange_command

        return lrange_command

    @pytest.fixture
    def store_with_list(self):
        """Create a store with a list for testing."""
        store = Store()
        # Add a list with 5 elements ["one", "two", "three", "four", "five"]
        store.set_key("mylist", ["one", "two", "three", "four", "five"])
        return store

    @pytest.mark.asyncio
    async def test_lrange_returns_entire_list(self, command, store_with_list):
        """Test that LRANGE returns the entire list when 0 to -1 is specified."""
        result = await command.execute("mylist", "0", "-1", store=store_with_list)
        assert result == ["one", "two", "three", "four", "five"]

    @pytest.mark.asyncio
    async def test_lrange_with_positive_indices(self, command, store_with_list):
        """Test LRANGE with positive start and end indices."""
        # First three elements (0-based index 0 to 2)
        result = await command.execute("mylist", "0", "2", store=store_with_list)
        assert result == ["one", "two", "three"]

        # Middle elements (1 to 3)
        result = await command.execute("mylist", "1", "3", store=store_with_list)
        assert result == ["two", "three", "four"]

    @pytest.mark.asyncio
    async def test_lrange_with_negative_indices(self, command, store_with_list):
        """Test LRANGE with negative indices (counting from the end)."""
        # Last two elements
        result = await command.execute("mylist", "-2", "-1", store=store_with_list)
        assert result == ["four", "five"]

        # From third to last to second to last
        result = await command.execute("mylist", "-3", "-2", store=store_with_list)
        assert result == ["three", "four"]

    @pytest.mark.asyncio
    async def test_lrange_with_out_of_range_indices(self, command, store_with_list):
        """Test LRANGE with indices that are out of range."""
        # Start index greater than list length
        result = await command.execute("mylist", "10", "20", store=store_with_list)
        assert result == []

        # End index greater than list length (should be capped at last index)
        result = await command.execute("mylist", "0", "100", store=store_with_list)
        assert result == ["one", "two", "three", "four", "five"]

    @pytest.mark.asyncio
    async def test_lrange_with_start_greater_than_end(self, command, store_with_list):
        """Test LRANGE with start index greater than end index."""
        result = await command.execute("mylist", "3", "1", store=store_with_list)
        assert result == []

    @pytest.mark.asyncio
    async def test_lrange_with_nonexistent_key(self, command, store_with_list):
        """Test LRANGE with a key that doesn't exist."""
        result = await command.execute("nonexistent", "0", "-1", store=store_with_list)
        assert result == []

    @pytest.mark.asyncio
    async def test_lrange_with_non_list_key(self, command):
        """Test LRANGE with a key that exists but is not a list."""
        store = Store()
        store.set_key("notalist", "I am a string, not a list")

        with pytest.raises(ValueError) as exc_info:
            await command.execute("notalist", "0", "-1", store=store)
        assert (
            "WRONGTYPE" in str(exc_info.value)
            or "wrong type" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_lrange_with_invalid_arguments(self, command, store_with_list):
        """Test LRANGE with invalid arguments."""
        # Not enough arguments
        with pytest.raises(ValueError) as exc_info:
            await command.execute("mylist", "0", store=store_with_list)
        assert "wrong number of arguments" in str(exc_info.value).lower()

        # Non-integer indices
        with pytest.raises(ValueError):
            await command.execute("mylist", "notanumber", "1", store=store_with_list)

        with pytest.raises(ValueError):
            await command.execute("mylist", "0", "notanumber", store=store_with_list)

    @pytest.mark.asyncio
    async def test_lrange_with_empty_list(self, command):
        """Test LRANGE with an empty list."""
        store = Store()
        store.set_key("emptylist", [])

        result = await command.execute("emptylist", "0", "-1", store=store)
        assert result == []
