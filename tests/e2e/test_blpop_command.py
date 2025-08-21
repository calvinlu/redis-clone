"""End-to-end tests for the BLPOP command."""
import asyncio

import pytest
from redis.exceptions import ResponseError, TimeoutError

from tests.e2e.base_e2e_test import BaseE2ETest


class TestBLPOPE2E(BaseE2ETest):
    """End-to-end tests for the BLPOP command."""

    @pytest.mark.asyncio
    async def test_blpop_basic_operations(self):
        """Test basic BLPOP operations."""
        # Test BLPOP on non-existent key with 0 timeout returns None immediately
        result = await self.execute_command("BLPOP", "nonexistent", "0")
        assert result is None, f"Expected None for non-existent key, got {result!r}"

        # Create a list
        await self.execute_command("RPUSH", "mylist", "one", "two")

        # Test BLPOP returns first element as a tuple (key, value)
        result = await self.execute_command("BLPOP", "mylist", "1")
        assert result == (
            "mylist",
            "one",
        ), f"Expected ('mylist', 'one'), got {result!r}"

        # Verify the element was removed
        result = await self.execute_command("LRANGE", "mylist", "0", "-1")
        assert result == ["two"], f"Expected ['two'], got {result!r}"

    @pytest.mark.asyncio
    async def test_blpop_timeout_behavior(self):
        """Test BLPOP timeout behavior and RESP2 format."""
        # Test BLPOP with 0.1 second timeout on empty list
        start_time = asyncio.get_event_loop().time()
        result = await self.execute_command("BLPOP", "emptylist", "0.1")
        end_time = asyncio.get_event_loop().time()

        # Should return None after timeout
        assert result is None, f"Expected None on timeout, got {result!r}"

        # Should have waited at least 0.1 seconds
        assert end_time - start_time >= 0.1, "BLPOP didn't wait for the full timeout"

    @pytest.mark.asyncio
    async def test_blpop_with_multiple_keys(self):
        """Test BLPOP with multiple keys."""

        # Create a task that will push to list2 after a short delay
        async def delayed_push():
            await asyncio.sleep(0.1)
            await self.execute_command("RPUSH", "list2", "hello")

        # Start the push in the background
        push_task = asyncio.create_task(delayed_push())

        try:
            # This should block until the push happens
            result = await self.execute_command("BLPOP", "list1", "list2", "list3", "1")
            assert result == (
                "list2",
                "hello",
            ), f"Expected ('list2', 'hello'), got {result!r}"
        finally:
            await push_task  # Ensure the background task is done

    @pytest.mark.asyncio
    async def test_blpop_with_existing_data(self):
        """Test BLPOP returns immediately when data exists."""
        # Add data to a list
        await self.execute_command("RPUSH", "mylist2", "quick", "response")

        # BLPOP should return immediately
        start_time = asyncio.get_event_loop().time()
        result = await self.execute_command("BLPOP", "mylist2", "1")
        end_time = asyncio.get_event_loop().time()

        assert result == (
            "mylist2",
            "quick",
        ), f"Expected ('mylist2', 'quick'), got {result!r}"
        assert (
            end_time - start_time < 0.1
        ), "BLPOP should return immediately when data exists"

    @pytest.mark.asyncio
    async def test_blpop_wrong_type(self):
        """Test BLPOP with wrong type raises an error."""
        # Create a string key
        await self.execute_command("SET", "mystring", "hello")

        # BLPOP should return an error
        with pytest.raises(ResponseError, match="WRONGTYPE"):
            await self.execute_command("BLPOP", "mystring", "0")
