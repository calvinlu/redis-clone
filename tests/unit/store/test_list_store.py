"""Unit tests for the ListStore class."""
from typing import List

import pytest

from app.store.list_store import ListStore


class TestListStore:
    """Test cases for ListStore operations."""

    @pytest.fixture
    def store(self) -> ListStore:
        """Create a fresh ListStore instance for each test."""
        return ListStore()

    @pytest.fixture
    def populated_store(self, store: ListStore) -> ListStore:
        """Fixture with a list containing ['a', 'b', 'c', 'd', 'e']."""
        store.rpush("mylist", "a", "b", "c", "d", "e")
        return store

    # Test RPUSH and basic LRANGE
    class TestRPushAndLRange:
        """Tests for RPUSH and basic LRANGE functionality."""

        def test_rpush_to_new_list(self, store: ListStore):
            """Test pushing elements to a new list."""
            assert store.rpush("mylist", "a", "b", "c") == 3
            assert store.lrange("mylist", 0, -1) == ["a", "b", "c"]

        def test_rpush_existing_list(self, populated_store: ListStore):
            """Test appending to an existing list."""
            assert populated_store.rpush("mylist", "f", "g") == 7
            assert populated_store.lrange("mylist", 0, -1) == [
                "a",
                "b",
                "c",
                "d",
                "e",
                "f",
                "g",
            ]

    # Test LRANGE with different index patterns
    class TestLRangeIndices:
        """Tests for LRANGE with various index patterns."""

        @pytest.mark.parametrize(
            "start,end,expected",
            [
                # Positive indices
                (0, 1, ["a", "b"]),
                (1, 3, ["b", "c", "d"]),
                # Negative indices
                (-3, -1, ["c", "d", "e"]),
                (-2, -1, ["d", "e"]),
                # Mixed indices
                (0, -1, ["a", "b", "c", "d", "e"]),  # All elements
                (1, -2, ["b", "c", "d"]),  # Positive start, negative end
                (-4, 3, ["b", "c", "d"]),  # Negative start, positive end
            ],
        )
        def test_lrange_various_indices(
            self, populated_store: ListStore, start: int, end: int, expected: List[str]
        ):
            """Test LRANGE with different index combinations."""
            assert populated_store.lrange("mylist", start, end) == expected

        @pytest.mark.parametrize(
            "start,end,expected",
            [
                # Out of bounds
                (0, 10, ["a", "b", "c", "d", "e"]),
                (10, 20, []),
                (-10, 1, ["a", "b"]),
                (-10, -6, []),  # Both beyond left boundary
            ],
        )
        def test_lrange_out_of_bounds(
            self, populated_store: ListStore, start: int, end: int, expected: List[str]
        ):
            """Test LRANGE with out-of-bounds indices."""
            assert populated_store.lrange("mylist", start, end) == expected

    # Test DELETE operation
    class TestDelete:
        """Tests for DELETE operation."""

        def test_delete_existing_key(self, populated_store: ListStore):
            """Test deleting an existing key."""
            assert populated_store.delete("mylist") is True
            assert populated_store.lrange("mylist", 0, -1) == []

        def test_delete_nonexistent_key(self, store: ListStore):
            """Test deleting a key that doesn't exist."""
            assert store.delete("nonexistent") is False

    # Test flushdb functionality
    class TestFlushDB:
        """Tests for flushdb functionality."""

        def test_flushdb_empty_store(self, store: ListStore):
            """Test flushdb on an empty store."""
            # Should not raise any exceptions
            store.flushdb()
            assert len(store.lists) == 0

        def test_flushdb_with_values(self, populated_store: ListStore):
            """Test flushdb removes all lists."""
            # Verify we have data first
            assert len(populated_store.lists) > 0

            # Perform flushdb
            populated_store.flushdb()

            # Verify all lists are removed
            assert len(populated_store.lists) == 0

            # Verify we can't access the list anymore
            assert populated_store.lrange("mylist", 0, -1) == []

        def test_flushdb_affects_only_current_store(self):
            """Test that flushdb only affects the current store instance."""
            # Create two stores with the same data
            store1 = ListStore()
            store2 = ListStore()

            store1.rpush("list1", "a", "b", "c")
            store2.rpush("list1", "x", "y", "z")

            # Flush store1
            store1.flushdb()

            # Verify store1 is empty
            assert len(store1.lists) == 0

            # Verify store2 still has its data
            assert len(store2.lists) == 1
            assert store2.lrange("list1", 0, -1) == ["x", "y", "z"]


class TestListStoreNormalization:
    """Test cases for ListStore index normalization methods."""

    @pytest.fixture
    def store(self) -> ListStore:
        """Create a fresh ListStore instance for each test."""
        return ListStore()

    # Parameterized tests for _normalize_start_index
    @pytest.mark.parametrize(
        "index,length,expected",
        [
            # Within bounds
            (2, 5, 2),  # Simple case
            (0, 5, 0),  # First element
            (4, 5, 4),  # Last element
            # Out of bounds (positive)
            (5, 5, 5),  # At boundary
            (10, 5, 5),  # Beyond boundary
            # Negative indices
            (-2, 5, 3),  # 5-2=3
            (-5, 5, 0),  # At boundary (negative)
            (-10, 5, 0),  # Beyond boundary (negative)
            # Empty list
            (0, 0, 0),
            (-1, 0, 0),
            (1, 0, 0),
        ],
    )
    def test_normalize_start_index(
        self, store: ListStore, index: int, length: int, expected: int
    ):
        """Test _normalize_start_index with various inputs."""

        # pylint: disable=protected-access

        assert store._normalize_start_index(index, length) == expected

    # Parameterized tests for _normalize_end_index
    @pytest.mark.parametrize(
        "index,length,expected",
        [
            # Within bounds
            (2, 5, 2),  # Simple case
            (0, 5, 0),  # First element
            (4, 5, 4),  # Last element
            # Out of bounds (positive)
            (4, 5, 4),  # At boundary
            (10, 5, 4),  # Beyond boundary
            # Negative indices
            (-1, 5, 4),  # Last element
            (-2, 5, 3),  # Second to last
            (-5, 5, 0),  # First element (negative)
            (-10, 5, -1),  # Beyond boundary (negative, returns -1 for empty range)
            # Empty list
            (0, 0, -1),
            (-1, 0, -1),
            (1, 0, -1),
        ],
    )
    def test_normalize_end_index(
        self, store: ListStore, index: int, length: int, expected: int
    ):
        """Test _normalize_end_index with various inputs."""

        # pylint: disable=protected-access

        assert store._normalize_end_index(index, length) == expected
