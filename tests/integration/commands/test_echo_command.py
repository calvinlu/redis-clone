"""Integration tests for the ECHO command."""
import pytest

from app.commands.echo_command import command as echo_command


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
        result = await command.execute("first", "second", "third")
        assert result == "first"

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
