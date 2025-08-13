"""Unit tests for the StringStore class."""
import time

import pytest

from app.store.string_store import StringStore


class TestStringStore:
    """Test cases for StringStore."""

    @pytest.fixture
    def store(self):
        """Create a fresh StringStore instance for each test."""
        return StringStore()

    def test_set_and_get(self, store):
        """Test basic set and get operations."""
        store.set("key1", "value1")
        assert store.get("key1") == "value1"

    def test_set_with_ttl(self, store):
        """Test setting a key with TTL."""
        store.set("temp", "value", ttl=100)  # 100ms TTL
        assert store.get("temp") == "value"

    def test_expired_key(self, store):
        """Test that expired keys return None."""
        store.set("temp", "value", ttl=1)  # Very short TTL
        time.sleep(0.1)  # Wait for expiration
        assert store.get("temp") is None

    def test_delete(self, store):
        """Test deleting a key."""
        store.set("key1", "value1")
        assert store.delete("key1") is True
        assert store.get("key1") is None
        assert store.delete("nonexistent") is False

    def test_flushdb_empty_store(self, store):
        """Test flushdb on an empty store."""
        # Should not raise any exceptions
        store.flushdb()
        assert len(store.values) == 0
        assert len(store.expirations) == 0

    def test_flushdb_with_values(self, store):
        """Test flushdb removes all keys and their expirations."""
        # Add some test data
        store.set("key1", "value1")
        store.set("key2", "value2", ttl=1000)
        store.set("key3", "value3")

        # Verify data exists
        assert len(store.values) == 3
        assert len(store.expirations) == 1  # Only key2 has TTL

        # Execute flushdb
        store.flushdb()

        # Verify all data is gone
        assert len(store.values) == 0
        assert len(store.expirations) == 0

        # Verify individual keys are gone
        assert store.get("key1") is None
        assert store.get("key2") is None
        assert store.get("key3") is None

    def test_flushdb_preserves_store_instance(self, store):
        """Test that flushdb doesn't recreate the store instance."""
        store_id = id(store)
        store.set("key1", "value1")

        store.flushdb()

        # The store instance should be the same
        assert id(store) == store_id
        # But it should be empty
        assert len(store.values) == 0
        assert len(store.expirations) == 0
