"""Unit tests for the BlockingQueueManager class."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.blocking.queue_manager import BlockingOperation, BlockingQueueManager


class TestBlockingQueueManager:
    """Test suite for BlockingQueueManager."""

    @pytest.fixture
    def manager(self):
        """Create a new BlockingQueueManager instance for each test."""
        return BlockingQueueManager()

    @pytest.mark.asyncio
    async def test_wait_for_push_immediate_data(self, manager):
        """Test that wait_for_push returns immediately when data is available."""
        # Simulate data being available immediately
        key = "test_key"
        value = "test_value"

        # Start the wait in the background
        task = asyncio.create_task(manager.wait_for_push([key], 1.0))

        # Allow the task to start
        await asyncio.sleep(0)

        # Simulate a push notification
        await manager.notify_push(key, value)

        # The task should complete immediately
        result_key, result_value = await asyncio.wait_for(task, timeout=0.1)
        assert result_key == key
        assert result_value == value

    @pytest.mark.asyncio
    async def test_wait_for_push_timeout(self, manager):
        """Test that wait_for_push times out correctly."""
        key = "test_key"

        # This should time out after 0.1 seconds
        result_key, result_value = await manager.wait_for_push([key], 0.1)

        assert result_key is None
        assert result_value is None

    @pytest.mark.asyncio
    async def test_wait_for_push_multiple_keys(self, manager):
        """Test that wait_for_push works with multiple keys."""
        keys = ["key1", "key2", "key3"]
        value = "test_value"

        # Start the wait in the background
        task = asyncio.create_task(manager.wait_for_push(keys, 1.0))

        # Allow the task to start
        await asyncio.sleep(0)

        # Simulate a push notification to the second key
        await manager.notify_push(keys[1], value)

        # The task should complete with the second key
        result_key, result_value = await asyncio.wait_for(task, timeout=0.1)
        assert result_key == keys[1]
        assert result_value == value

    @pytest.mark.asyncio
    async def test_shutdown_cancels_pending_operations(self, manager):
        """Test that shutdown cancels all pending operations."""
        key = "test_key"

        # Start a blocking operation
        task = asyncio.create_task(manager.wait_for_push([key], 10.0))

        # Allow the task to start
        await asyncio.sleep(0)

        # Shutdown should cancel the operation
        await manager.shutdown()

        # The task should be cancelled
        with pytest.raises(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_notify_push_no_waiters(self, manager):
        """Test that notify_push works when there are no waiters."""
        # This should not raise any exceptions
        result = await manager.notify_push("nonexistent_key", "value")
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_after_operation(self, manager):
        """Test that operations are properly cleaned up after completion."""
        key = "test_key"
        value = "test_value"

        # Start and complete an operation
        task = asyncio.create_task(manager.wait_for_push([key], 0.1))
        await asyncio.sleep(0)
        await manager.notify_push(key, value)

        # Wait for the operation to complete
        await task

        # The operation should be cleaned up
        assert not manager.waiting_operations
        assert not manager.active_operations
