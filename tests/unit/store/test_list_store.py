"""Unit tests for the ListStore class."""
import pytest

from app.store.list_store import ListStore


class TestListStore:
    """Test cases for ListStore."""

    @pytest.fixture
    def store(self):
        """Create a fresh ListStore instance for each test."""
        return ListStore()

    def test_rpush_and_lrange(self, store):
        """Test basic RPUSH and LRANGE operations."""
        # Test pushing to new list
        assert store.rpush("mylist", "a", "b", "c") == 3
        assert store.lrange("mylist", 0, -1) == ["a", "b", "c"]

        # Test pushing more elements
        assert store.rpush("mylist", "d", "e") == 5
        assert store.lrange("mylist", 0, -1) == ["a", "b", "c", "d", "e"]

    def test_lrange_indices(self, store):
        """Test LRANGE with different index values."""
        store.rpush("mylist", "a", "b", "c", "d", "e")

        # Test positive indices
        assert store.lrange("mylist", 0, 1) == ["a", "b"]
        assert store.lrange("mylist", 1, 3) == ["b", "c", "d"]

        # Test negative indices (from end)
        assert store.lrange("mylist", -3, -1) == ["c", "d", "e"]
        assert store.lrange("mylist", -2, -1) == ["d", "e"]

        # Test out of bounds
        assert store.lrange("mylist", 0, 10) == ["a", "b", "c", "d", "e"]
        assert store.lrange("mylist", 10, 20) == []

    def test_delete(self, store):
        """Test deleting a list."""
        store.rpush("mylist", "a", "b", "c")
        assert store.delete("mylist") is True
        assert store.lrange("mylist", 0, -1) == []
        assert store.delete("nonexistent") is False
