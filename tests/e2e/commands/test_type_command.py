"""End-to-end tests for the Redis TYPE command."""
import pytest

from tests.e2e.base_e2e_test import BaseE2ETest


class TestTypeCommandE2E(BaseE2ETest):
    """End-to-end tests for the TYPE command."""

    @pytest.mark.asyncio
    async def test_type_command_returns_none_for_non_existing_key(self):
        """Test that TYPE returns 'none' for non-existing keys."""
        result = await self._test_client.execute_command("TYPE", "nonexistent_key")
        assert result == b"none"

    @pytest.mark.asyncio
    async def test_type_command_returns_type_for_existing_key(self):
        """Test that TYPE returns the correct type for existing keys."""
        # Test string type
        await self._test_client.set("str_key", "value")
        result = await self._test_client.execute_command("TYPE", "str_key")
        assert result == b"string"

        # Test list type
        await self._test_client.lpush("list_key", "value1", "value2")
        result = await self._test_client.execute_command("TYPE", "list_key")
        assert result == b"list"

    @pytest.mark.asyncio
    async def test_type_command_with_multiple_keys(self):
        """Test TYPE command with multiple keys of different types."""
        # Set up different types of keys
        await self._test_client.set("key1", "value1")
        await self._test_client.lpush("key2", "item1", "item2")

        # Test each key's type
        assert await self._test_client.execute_command("TYPE", "key1") == b"string"
        assert await self._test_client.execute_command("TYPE", "key2") == b"list"
        assert await self._test_client.execute_command("TYPE", "nonexistent") == b"none"

    @pytest.mark.asyncio
    async def test_type_command_error_cases(self):
        """Test TYPE command with wrong number of arguments."""
        with pytest.raises(Exception) as exc_info:
            await self._test_client.execute_command("TYPE")
        assert "wrong number of arguments" in str(exc_info.value).lower()

        with pytest.raises(Exception) as exc_info:
            await self._test_client.execute_command("TYPE", "key1", "key2")
        assert "wrong number of arguments" in str(exc_info.value).lower()
