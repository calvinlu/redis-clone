"""Integration tests for the PING command."""
import pytest

from app.commands.ping_command import command as ping_command
from app.store.store import Store


class TestPingCommand:
    """Test cases for the PING command."""

    @pytest.fixture
    def command(self):
        """Get the ping command instance."""

        return ping_command

    @pytest.mark.asyncio
    async def test_ping_returns_pong(self, command):
        """Test that PING returns 'PONG'."""
        result = await command.execute()
        assert result == "PONG"

    @pytest.mark.asyncio
    async def test_ping_ignores_arguments(self, command):
        """Test that PING ignores any arguments and always returns 'PONG'."""
        # Test with no arguments
        result = await command.execute()
        assert result == "PONG"

        # Test with one argument
        result = await command.execute("hello")
        assert result == "PONG"

        # Test with multiple arguments
        result = await command.execute("arg1", "arg2", "arg3")
        assert result == "PONG"

    @pytest.mark.asyncio
    async def test_ping_with_store_parameter(self, command):
        """Test that PING works with or without store parameter."""
        # Test without store parameter
        result = await command.execute()
        assert result == "PONG"

        # Test with store parameter (should be ignored)
        store = Store()
        result = await command.execute(store=store)
        assert result == "PONG"

    @pytest.mark.asyncio
    async def test_ping_with_mixed_arguments(self, command):
        """Test PING with mixed argument types."""
        # Test with different types of arguments
        result = await command.execute(123)  # integer
        assert result == "PONG"

        result = await command.execute(None)  # None
        assert result == "PONG"

        result = await command.execute("")  # empty string
        assert result == "PONG"

        result = await command.execute("PING")  # string "PING"
        assert result == "PONG"
