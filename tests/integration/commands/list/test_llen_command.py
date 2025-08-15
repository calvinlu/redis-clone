"""Integration tests for the LLEN command."""
import pytest

from app.commands.dispatcher import CommandDispatcher
from app.commands.list.llen_command import command as llen_command
from app.commands.list.rpush_command import command as rpush_command
from app.commands.string.set_command import command as set_command
from app.store import Store


class TestLLenCommandIntegration:
    """Integration tests for LLEN command with real store and dispatcher."""

    @pytest.fixture
    def store(self):
        """Return a new Store instance for each test."""
        return Store()

    @pytest.fixture
    def dispatcher(self, store):
        """Return a CommandDispatcher with a store instance and registered commands."""
        dispatcher = CommandDispatcher(store)
        dispatcher.register(llen_command)
        dispatcher.register(rpush_command)
        dispatcher.register(set_command)  # Needed for the SET command test
        return dispatcher

    @pytest.mark.asyncio
    async def test_llen_returns_zero_for_nonexistent_key(self, dispatcher):
        """Test that LLEN returns 0 for a non-existent key."""
        result = await dispatcher.execute("LLEN", "nonexistent")
        assert result == 0

    @pytest.mark.asyncio
    async def test_llen_returns_correct_length(self, dispatcher):
        """Test that LLEN returns the correct length of an existing list."""
        # First add some items to the list
        await dispatcher.execute("RPUSH", "mylist", "one", "two", "three")

        # Test LLEN
        result = await dispatcher.execute("LLEN", "mylist")
        assert result == 3

    @pytest.mark.asyncio
    async def test_llen_with_wrong_type_raises_error(self, dispatcher):
        """Test that LLEN with a non-list key raises an error."""
        # Set a string value
        await dispatcher.execute("SET", "mystring", "value")

        # Test LLEN on string should raise error
        with pytest.raises(TypeError, match="WRONGTYPE"):
            await dispatcher.execute("LLEN", "mystring")

    @pytest.mark.asyncio
    async def test_llen_with_wrong_number_of_arguments(self, dispatcher):
        """Test that LLEN with wrong number of arguments raises an error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            await dispatcher.execute("LLEN")

        with pytest.raises(ValueError, match="wrong number of arguments"):
            await dispatcher.execute("LLEN", "key1", "key2")
