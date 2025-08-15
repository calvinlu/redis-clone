"""End-to-end tests for the GET command."""
import pytest
from redis.exceptions import ResponseError

from tests.e2e.base_e2e_test import BaseE2ETest


class TestGetE2E(BaseE2ETest):
    """End-to-end tests for the GET command."""

    @pytest.mark.asyncio
    async def test_get_basic_operations(self):
        """Test basic GET operations."""
        # Test getting a non-existent key returns None
        result = await self.execute_command("GET", "nonexistent")
        assert result is None, f"Expected None, got {result!r}"

        # Set a key and get it back
        await self.execute_command("SET", "mykey", "hello")
        result = await self.execute_command("GET", "mykey")
        assert result == "hello", f"Expected 'hello', got {result!r}"

        # Overwrite the key and get the new value
        await self.execute_command("SET", "mykey", "world")
        result = await self.execute_command("GET", "mykey")
        assert result == "world", f"Expected 'world', got {result!r}"

    @pytest.mark.asyncio
    async def test_get_with_expired_key(self):
        """Test GET with an expired key returns None."""
        # Set a key with 100ms TTL
        await self.execute_command("SET", "tempkey", "value", "PX", "100")

        # Should be able to get it immediately
        result = await self.execute_command("GET", "tempkey")
        assert result == "value", f"Expected 'value', got {result!r}"

        # Wait for TTL to expire
        import asyncio

        await asyncio.sleep(0.15)  # 150ms to be safe

        # Should be expired now
        result = await self.execute_command("GET", "tempkey")
        assert result is None, f"Expected None, got {result!r}"

    @pytest.mark.asyncio
    async def test_get_invalid_arguments(self):
        """Test GET with invalid arguments."""
        # No key provided
        with pytest.raises(ResponseError, match="wrong number of arguments"):
            await self.execute_command("GET")

        # Too many arguments
        with pytest.raises(ResponseError, match="wrong number of arguments"):
            await self.execute_command("GET", "key1", "key2")
