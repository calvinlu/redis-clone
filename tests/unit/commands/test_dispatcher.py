"""Unit tests for the CommandDispatcher class using pytest."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.commands import Command, CommandDispatcher
from app.store import Store


class TestCommand(Command):
    """Test command implementation for testing the dispatcher."""

    name = "TEST"

    async def execute(self, *args: str, **kwargs: Any) -> str:
        """Return a test response with the provided arguments."""
        return f"TEST:{':'.join(args)}" if args else "TEST"


class TestErrorCommand(Command):
    """Test command that raises an exception."""

    name = "ERROR"

    async def execute(self, *args: str, **kwargs: Any) -> str:
        """Raise a ValueError."""
        raise ValueError("Test error")


@pytest_asyncio.fixture
async def store():
    """Fixture providing a mock store."""
    return MagicMock(spec=Store)


@pytest_asyncio.fixture
async def dispatcher(store):
    """Fixture providing a CommandDispatcher with a mock store.

    Args:
        store: The store instance to use (injected by pytest)
    """
    return CommandDispatcher(store)


class TestCommandDispatcher:
    """Test suite for the CommandDispatcher class using pytest-asyncio."""

    async def test_register_command(self, dispatcher):
        """Test registering a command with the dispatcher."""
        command = TestCommand()
        dispatcher.register(command)
        assert "TEST" in dispatcher.commands
        assert dispatcher.commands["TEST"] is command

    async def test_register_invalid_command(self, dispatcher):
        """Test that registering a non-Command raises TypeError."""
        with pytest.raises(TypeError):
            dispatcher.register("not a command")  # type: ignore

    async def test_execute_command(self, dispatcher):
        """Test executing a registered command."""
        command = TestCommand()
        dispatcher.register(command)
        result = await dispatcher.execute("test", "arg1", "arg2")
        assert result == "TEST:arg1:arg2"

    async def test_execute_command_case_insensitive(self, dispatcher):
        """Test that command names are case-insensitive."""
        command = TestCommand()
        dispatcher.register(command)
        result = await dispatcher.execute("TeSt")
        assert result == "TEST"

    async def test_execute_unknown_command(self, dispatcher):
        """Test that executing an unknown command raises ValueError."""
        with pytest.raises(ValueError, match="unknown command"):
            await dispatcher.execute("UNKNOWN")

    async def test_execute_command_error_handling(self, dispatcher):
        """Test that command errors are properly propagated."""
        command = TestErrorCommand()
        dispatcher.register(command)
        with pytest.raises(ValueError, match="Test error"):
            await dispatcher.execute("error")

    async def test_execute_with_store_injection(self, dispatcher, store):
        """Test that the store is properly injected into commands."""
        mock_command = AsyncMock(spec=Command)
        mock_command.name = "MOCK"
        mock_command.execute.return_value = "MOCK_RESPONSE"
        dispatcher.register(mock_command)

        result = await dispatcher.execute("mock", "arg1", "arg2")

        mock_command.execute.assert_awaited_once_with("arg1", "arg2", store=store)
        assert result == "MOCK_RESPONSE"
