"""Base class for command integration tests."""
from typing import Any

import pytest

from app.commands.dispatcher import CommandDispatcher
from app.connection import create_dispatcher
from app.store import Store


class BaseCommandTest:
    """Base class for command integration tests."""

    @pytest.fixture
    def store(self) -> Store:
        """Return a fresh store instance for each test."""
        return Store()

    @pytest.fixture
    def dispatcher(self, store: Store) -> CommandDispatcher:
        """Return a command dispatcher with all commands registered."""
        return create_dispatcher(store)

    async def execute_command(
        self, dispatcher: CommandDispatcher, command: str, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute a command and return its result."""
        return await dispatcher.execute(command, *args, **kwargs)
