"""End-to-end tests for the SET command."""
import asyncio

import pytest
from redis.exceptions import ResponseError

from tests.e2e.base_e2e_test import BaseE2ETest


class TestSetE2E(BaseE2ETest):
    """End-to-end tests for the SET command."""

    @pytest.mark.asyncio
    async def test_set_basic_operations(self):
        """Test basic SET operations."""
        # Test setting a new key
        result = await self.execute_command("SET", "mykey", "hello")
        assert result is True, f"Expected True, got {result!r}"

        # Test getting the value back
        get_result = await self.execute_command("GET", "mykey")
        assert get_result == "hello", f"Expected 'hello', got {get_result!r}"

    @pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test SET with PX (TTL in milliseconds) option."""
        # Set key with 100ms TTL
        result = await self.execute_command("SET", "tempkey", "value", "PX", "100")
        assert result is True, f"Expected True, got {result!r}"

        # Should be able to get it immediately
        get_result = await self.execute_command("GET", "tempkey")
        assert get_result == "value", f"Expected 'value', got {get_result!r}"

        # Wait for TTL to expire
        await asyncio.sleep(0.15)  # 150ms to be safe

        # Should be expired now
        get_result = await self.execute_command("GET", "tempkey")
        assert get_result is None, f"Expected None, got {get_result!r}"

    @pytest.mark.asyncio
    async def test_set_invalid_arguments(self):
        """Test SET with invalid arguments."""
        # Not enough arguments
        with pytest.raises(ResponseError, match="wrong number of arguments"):
            await self.execute_command("SET", "key")

        # Invalid TTL format (non-numeric)
        with pytest.raises(ResponseError, match="invalid expire time"):
            await self.execute_command("SET", "key", "value", "PX", "notanumber")

        # Invalid TTL (negative)
        with pytest.raises(ResponseError, match="invalid expire time"):
            await self.execute_command("SET", "key", "value", "PX", "-100")

        # Missing TTL value
        with pytest.raises(ResponseError, match="syntax error"):
            await self.execute_command("SET", "key", "value", "PX")

        # Unsupported option
        with pytest.raises(ResponseError, match="syntax error"):
            await self.execute_command("SET", "key", "value", "INVALID")
