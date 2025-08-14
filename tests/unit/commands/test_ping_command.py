"""Unit tests for the Redis PING command."""
import pytest

from app.commands.ping_command import PingCommand


class TestPingCommand:
    """Test cases for the PingCommand class."""

    @pytest.fixture
    def command(self):
        """Create a PingCommand instance for testing."""
        return PingCommand()

    @pytest.mark.asyncio
    async def test_name_returns_uppercase_ping(self, command):
        """Test that the name property returns 'PING' in uppercase."""
        assert command.name == "PING"

    @pytest.mark.asyncio
    async def test_execute_returns_pong(self, command):
        """Test that execute always returns 'PONG' regardless of arguments."""
        # Test with no arguments
        result = await command.execute()
        assert result == "PONG"

        # Test with arguments (should be ignored)
        result = await command.execute("arg1", "arg2", "arg3")
        assert result == "PONG"

    @pytest.mark.asyncio
    async def test_execute_ignores_all_arguments(self, command):
        """Test that execute ignores all arguments and always returns 'PONG'."""
        # Test with different types of arguments
        result = await command.execute("test")
        assert result == "PONG"

        result = await command.execute(123)
        assert result == "PONG"

        result = await command.execute(None)
        assert result == "PONG"

        result = await command.execute("")
        assert result == "PONG"

    @pytest.mark.asyncio
    async def test_execute_with_store_parameter(self, command):
        """Test that execute works with or without store parameter."""
        # Test without store parameter
        result = await command.execute()
        assert result == "PONG"

        # Test with store parameter (should be ignored)
        result = await command.execute(store=None)
        assert result == "PONG"
