"""Unit tests for the Redis ECHO command."""
import pytest

from app.commands.echo_command import EchoCommand


class TestEchoCommand:
    """Test cases for the EchoCommand class."""

    @pytest.fixture
    def command(self):
        """Create an EchoCommand instance for testing."""
        return EchoCommand()

    @pytest.mark.asyncio
    async def test_name_returns_uppercase_echo(self, command):
        """Test that the name property returns 'ECHO' in uppercase."""
        assert command.name == "ECHO"

    @pytest.mark.asyncio
    async def test_execute_returns_same_message(self, command):
        """Test that execute returns the same message that was passed in."""
        # Test with a simple string
        result = await command.execute("Hello, World!")
        assert result == "Hello, World!"

        # Test with a number (should be converted to string)
        result = await command.execute("123")
        assert result == "123"

        # Test with special characters
        result = await command.execute("!@#$%^&*()")
        assert result == "!@#$%^&*()"

    @pytest.mark.asyncio
    async def test_execute_raises_error_with_no_arguments(self, command):
        """Test that execute raises ValueError when no arguments are provided."""
        with pytest.raises(ValueError) as exc_info:
            await command.execute()
        assert "wrong number of arguments for 'echo' command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_handles_multiple_arguments(self, command):
        """Test that execute uses only the first argument and ignores others."""
        # Should only use the first argument and ignore the rest
        with pytest.raises(ValueError) as exc_info:
            await command.execute("first", "second", "third")
        assert "wrong number of arguments for 'echo' command" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_handles_whitespace(self, command):
        """Test that execute handles messages with whitespace correctly."""
        result = await command.execute("Hello\nWorld")
        assert result == "Hello\nWorld"

        result = await command.execute("  leading and trailing spaces  ")
        assert result == "  leading and trailing spaces  "

    @pytest.mark.asyncio
    async def test_execute_handles_empty_string(self, command):
        """Test that execute handles empty string as a valid message."""
        result = await command.execute("")
        assert result == ""
