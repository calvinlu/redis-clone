"""Unit tests for the main Store class."""
import pytest

from app.store.store import Store


class TestStore:
    """Test cases for the main Store class."""

    @pytest.fixture
    def store(self):
        """Create a fresh Store instance for each test."""
        return Store()

    def test_set_and_get_string(self, store):
        """Test setting and getting string values."""
        store.set_key("str_key", "value")
        assert store.get_key("str_key") == "value"

    def test_rpush_and_lrange(self, store):
        """Test list operations."""
        # Test pushing to a list
        assert store.rpush("mylist", "a", "b", "c") == 3
        assert store.lrange("mylist", 0, -1) == ["a", "b", "c"]

    def test_type_safety(self, store):
        """Test that type safety is enforced."""
        # Create a string key
        store.set_key("mykey", "value")

        # Try to use it as a list - should raise TypeError
        with pytest.raises(TypeError):
            store.rpush("mykey", "a")

        # Create a list key
        store.rpush("mylist", "a")

        # Try to use it as a string - should raise TypeError
        with pytest.raises(TypeError):
            store.get_key("mylist")

    def test_delete_key(self, store):
        """Test deleting keys."""
        store.set_key("key1", "value1")
        store.rpush("list1", "a", "b")

        assert store.delete_key("key1") is True
        assert store.get_key("key1") is None

        assert store.delete_key("list1") is True
        # After deletion, lrange should return an empty list for non-existent keys
        assert store.lrange("list1", 0, -1) == []
