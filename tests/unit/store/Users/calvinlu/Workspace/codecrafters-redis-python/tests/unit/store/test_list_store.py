"""Tests for LPOP command"""
from app.store import ListStore


class TestLPop:
    """Tests for LPOP functionality."""

    def test_lpop_from_empty_list(self, store: ListStore):
        """Test LPOP on non-existent key returns -1."""
        assert store.lpop("nonexistent") == None

    def test_lpop_removes_and_returns_first_element(self, store: ListStore):
        """Test LPOP removes and returns the first element."""
        # Initial list is ['a', 'b', 'c', 'd', 'e']
        store.rpush("mylist", "a", "b", "c", "d", "e")
        result = store.lpop("mylist")
        assert result == "a"
        assert store.lrange("mylist", 0, -1) == ["b", "c", "d", "e"]

    def test_lpop_until_empty(self, store: ListStore):
        """Test LPOP until list is empty."""
        # Initial list is ['a', 'b', 'c', 'd', 'e']
        expected = ["a", "b", "c", "d", "e"]
        store.rpush("mylist", "a", "b", "c", "d", "e")
        for i in range(5):
            result = store.lpop("mylist")
            assert result == expected[i]

        # List should now be empty
        assert store.lpop("mylist") == None
        assert store.lrange("mylist", 0, -1) == []

    def test_lpop_after_rpush(self, store: ListStore):
        """Test LPOP after RPUSH operations."""
        store.rpush("mylist", "x", "y", "z")
        assert store.lpop("mylist") == "x"
        assert store.lpop("mylist") == "y"
        assert store.lrange("mylist", 0, -1) == ["z"]
