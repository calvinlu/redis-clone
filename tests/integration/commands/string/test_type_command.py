"""Integration tests for the Redis TYPE command."""
import pytest

from app.store import Store


class TestTypeCommandIntegration:
    """Integration tests for the TYPE command."""

    @pytest.mark.asyncio
    async def test_type_command_returns_none_for_non_existing_key(self):
        """Test that TYPE returns 'none' for non-existing keys."""
        store = Store()
        result = await store.type("nonexistent_key")
        assert result == "none"

    @pytest.mark.asyncio
    async def test_type_command_returns_type_for_existing_key(self):
        """Test that TYPE returns the correct type for existing keys."""
        store = Store()

        # Test string type
        await store.set("str_key", "value")
        assert await store.type("str_key") == "string"

        # Test list type
        await store.lpush("list_key", ["value1", "value2"])
        assert await store.type("list_key") == "list"

        # Test multiple keys with different types
        await store.set("another_str", "hello")
        await store.lpush("another_list", [1, 2, 3])

        assert await store.type("another_str") == "string"
        assert await store.type("another_list") == "list"
