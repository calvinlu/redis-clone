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


class TestListStoreNormalization:
    """Test cases for ListStore index normalization methods."""

    @pytest.fixture
    def store(self):
        """Create a fresh ListStore instance for each test."""
        return ListStore()

    # Test cases for _normalize_start_index
    def test_normalize_start_positive_within_bounds(self, store):
        """Test normalizing start index within bounds."""
        assert store._normalize_start_index(2, 5) == 2

    def test_normalize_start_positive_out_of_bounds(self, store):
        """Test normalizing start index beyond list length."""
        assert store._normalize_start_index(5, 5) == 5  # At boundary
        assert store._normalize_start_index(10, 5) == 5  # Beyond boundary

    def test_normalize_start_negative_within_bounds(self, store):
        """Test normalizing negative start index within bounds."""
        assert store._normalize_start_index(-2, 5) == 3  # 5-2=3

    def test_normalize_start_negative_out_of_bounds(self, store):
        """Test normalizing negative start index beyond list start."""
        assert store._normalize_start_index(-5, 5) == 0  # At boundary
        assert store._normalize_start_index(-10, 5) == 0  # Beyond boundary

    def test_normalize_start_empty_list(self, store):
        """Test normalizing start index with empty list."""
        assert store._normalize_start_index(0, 0) == 0
        assert store._normalize_start_index(-1, 0) == 0
        assert store._normalize_start_index(1, 0) == 0

    # Test cases for _normalize_end_index
    def test_normalize_end_positive_within_bounds(self, store):
        """Test normalizing end index within bounds."""
        assert store._normalize_end_index(2, 5) == 2

    def test_normalize_end_positive_out_of_bounds(self, store):
        """Test normalizing end index beyond list length."""
        assert store._normalize_end_index(4, 5) == 4  # At boundary
        assert store._normalize_end_index(10, 5) == 4  # Beyond boundary

    def test_normalize_end_negative_within_bounds(self, store):
        """Test normalizing negative end index within bounds."""
        assert store._normalize_end_index(-1, 5) == 4  # 5-1=4 (last element)
        assert store._normalize_end_index(-2, 5) == 3  # 5-2=3

    def test_normalize_end_negative_out_of_bounds(self, store):
        """Test normalizing negative end index beyond list start."""
        assert store._normalize_end_index(-5, 5) == 0  # At boundary
        assert store._normalize_end_index(-10, 5) == -1  # Beyond boundary (empty range)

    def test_normalize_end_empty_list(self, store):
        """Test normalizing end index with empty list."""
        assert store._normalize_end_index(0, 0) == -1
        assert store._normalize_end_index(-1, 0) == -1
        assert store._normalize_end_index(1, 0) == -1
