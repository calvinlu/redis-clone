"""Unit tests for the Store class."""

import pytest

from app.store.store import Store


@pytest.fixture
def store():
    """Create a new Store instance for testing."""
    return Store()


def test_set_and_get_key(store):
    """Test that setting a key-value pair and then retrieving it returns the correct value."""
    store.set_key("name", "Alice")
    assert store.get_key("Alice") == "Alice"


def test_get_nonexistent_key(store):
    """Test that getting a non-existent key returns None."""
    assert store.get_key("Bob") is None


def test_empty_key(store):
    """Test that the store can handle empty string as a key."""
    store.set_key("", "empty key")
    assert store.get_key("") == "empty key"


def test_none_value(store):
    """
    Store should return back empty string when no value is set for the key.
    """
    store.set_key("null", None)
    assert store.get_key("null") == ""
