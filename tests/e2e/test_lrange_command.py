"""End-to-end tests for the LRANGE command."""
import pytest

from tests.e2e.test_commands import TestCommandResponses


class TestLRangeCommand(TestCommandResponses):
    """Tests for the LRANGE command."""

    @pytest.mark.asyncio
    async def test_lrange_basic_operations(self, redis_client):
        """Test basic LRANGE operations."""
        reader, writer = redis_client

        # First, create a list using RPUSH
        await self.send_command(
            reader, writer, "RPUSH", "mylist", "one", "two", "three"
        )

        # Test getting the full list
        response = await self.send_command(
            reader, writer, "LRANGE", "mylist", "0", "-1"
        )
        assert (
            response == b"*3\r\n$3\r\none\r\n$3\r\ntwo\r\n$5\r\nthree\r\n"
        ), f"Expected full list, got {response!r}"

        # Test getting a subset of the list
        response = await self.send_command(reader, writer, "LRANGE", "mylist", "0", "1")
        assert (
            response == b"*2\r\n$3\r\none\r\n$3\r\ntwo\r\n"
        ), f"Expected first two elements, got {response!r}"

        # Test getting a single element
        response = await self.send_command(reader, writer, "LRANGE", "mylist", "0", "0")
        assert (
            response == b"*1\r\n$3\r\none\r\n"
        ), f"Expected first element, got {response!r}"

        # Test with negative indices
        response = await self.send_command(
            reader, writer, "LRANGE", "mylist", "-2", "-1"
        )
        assert (
            response == b"*2\r\n$3\r\ntwo\r\n$5\r\nthree\r\n"
        ), f"Expected last two elements, got {response!r}"

    @pytest.mark.asyncio
    async def test_lrange_out_of_bounds(self, redis_client):
        """Test LRANGE with out-of-bounds indices."""
        reader, writer = redis_client

        # Create a list with 3 elements
        await self.send_command(reader, writer, "RPUSH", "mylist", "a", "b", "c")

        # Start index > end index (should return empty list)
        response = await self.send_command(reader, writer, "LRANGE", "mylist", "2", "1")
        assert response == b"*0\r\n", f"Expected empty list, got {response!r}"

        # Both indices out of bounds (beyond end)
        response = await self.send_command(
            reader, writer, "LRANGE", "mylist", "5", "10"
        )
        assert response == b"*0\r\n", f"Expected empty list, got {response!r}"

    @pytest.mark.asyncio
    async def test_lrange_wrong_type(self, redis_client):
        """Test LRANGE on a key with a different type returns an error."""
        reader, writer = redis_client

        # Create a string key
        await self.send_command(reader, writer, "SET", "mystring", "hello")

        # Try to use LRANGE on a string key
        response = await self.send_command(
            reader, writer, "LRANGE", "mystring", "0", "-1"
        )
        assert response.startswith(
            b"-ERR WRONGTYPE"
        ), f"Expected WRONGTYPE error, got {response!r}"

    @pytest.mark.asyncio
    async def test_lrange_nonexistent_key(self, redis_client):
        """Test LRANGE on a non-existent key returns an empty list."""
        reader, writer = redis_client

        # Try to use LRANGE on a non-existent key
        response = await self.send_command(
            reader, writer, "LRANGE", "nonexistent", "0", "-1"
        )
        assert response == b"*0\r\n", f"Expected empty list, got {response!r}"
