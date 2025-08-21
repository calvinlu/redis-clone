"""Integration tests for the BLPOP command."""
import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.commands.list.blpop_command import BLPopCommand
from app.store import Store


class TestBLPopCommand:
    """Test suite for the BLPOP command."""

    @pytest.fixture
    def store(self):
        """Create a new Store instance for each test."""
        return Store()

    @pytest.fixture
    def command(self):
        """Create a new BLPopCommand instance for each test."""
        return BLPopCommand()

    @pytest.mark.asyncio
    async def test_blpop_with_existing_data(self, command, store):
        """Test BLPOP with existing data returns immediately."""
        # Setup: Add data to a list
        key = "mylist"
        value = "hello"
        store.rpush(key, value)

        # Execute BLPOP with a timeout
        result = await command.execute(key, "1", store=store)

        # Verify: Should return the popped element
        assert result == [key, value]

        # The list should now be empty
        assert store.llen(key) == 0

    @pytest.mark.asyncio
    async def test_blpop_with_multiple_keys(self, command, store):
        """Test BLPOP with multiple keys returns from first non-empty list."""
        # Setup: Add data to the second list
        key1, key2 = "list1", "list2"
        value = "hello"
        store.rpush(key2, value)  # Only add to the second list

        # Execute BLPOP with both keys and a timeout
        result = await command.execute(key1, key2, "1", store=store)

        # Verify: Should return the element from the second list
        assert result == [key2, value]

    @pytest.mark.asyncio
    async def test_blpop_blocks_until_data(self, command, store):
        """Test BLPOP blocks until data is available."""
        key = "mylist"
        value = "hello"

        # Start BLPOP in the background
        task = asyncio.create_task(command.execute(key, "1", store=store))

        # Allow the task to start
        await asyncio.sleep(0)

        # Add data to the list
        store.rpush(key, value)

        # The task should now complete
        result = await asyncio.wait_for(task, timeout=0.1)
        assert result == [key, value]

    @pytest.mark.asyncio
    async def test_blpop_timeout(self, command, store):
        """Test BLPOP with a timeout returns None if no data is available."""
        key = "mylist"

        # Execute BLPOP with a short timeout
        result = await command.execute(key, "0.1", store=store)

        # Should return None after the timeout
        assert result is None

    @pytest.mark.asyncio
    async def test_blpop_wrong_type(self, command, store):
        """Test BLPOP with a key that's not a list raises an error."""
        key = "mystring"
        # Use the string store to set a non-list value
        store.stores["string"].set(key, "not a list")
        store.key_types[key] = "string"

        with pytest.raises(TypeError) as excinfo:
            await command.execute(key, "1", store=store)

        assert "WRONGTYPE" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_blpop_invalid_arguments(self, command, store):
        """Test BLPOP with invalid arguments raises an error."""
        # No keys provided
        with pytest.raises(ValueError) as excinfo:
            await command.execute("1", store=store)  # Only timeout, no keys
        assert "wrong number of arguments" in str(excinfo.value).lower()

        # Invalid timeout
        with pytest.raises(ValueError) as excinfo:
            await command.execute("mylist", "not_a_number", store=store)
        assert "timeout is not a float" in str(excinfo.value).lower()

        # Negative timeout
        with pytest.raises(ValueError) as excinfo:
            await command.execute("mylist", "-1", store=store)
        assert "timeout is negative" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_blpop_concurrent_clients(self, command, store):
        """Test BLPOP with multiple clients waiting on the same key."""
        key = "mylist"

        # Start multiple BLPOP operations
        tasks = [
            asyncio.create_task(command.execute(key, "1", store=store))
            for _ in range(3)
        ]

        # Allow tasks to start
        await asyncio.sleep(0)

        # Push one value - only one client should be unblocked
        store.rpush(key, "value1")

        # Wait a bit for the first task to complete
        done, pending = await asyncio.wait(
            tasks, timeout=0.1, return_when=asyncio.FIRST_COMPLETED
        )

        # One task should be done, others still pending
        assert len(done) == 1
        assert len(pending) == 2

        # The completed task should have the value
        result = done.pop().result()
        assert result == [key, "value1"]

        # Push another value
        store.rpush(key, "value2")

        # Wait for the second task to complete
        done, pending = await asyncio.wait(
            pending, timeout=0.1, return_when=asyncio.FIRST_COMPLETED
        )

        # One more task should be done
        assert len(done) == 1
        assert len(pending) == 1

        # The second completed task should have the second value
        result = done.pop().result()
        assert result == [key, "value2"]

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
