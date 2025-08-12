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
