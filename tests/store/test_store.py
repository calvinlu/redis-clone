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
    assert store.get_key("name") == "Alice"


def test_get_nonexistent_key(store):
    """Test that getting a non-existent key returns None."""
    assert store.get_key("Bob") is None


def test_empty_key(store):
    """Test that the store can handle empty string as a key."""
    store.set_key("", "empty key")
    assert store.get_key("") == "empty key"


def test_none_value(store):
    """Test that setting a key to None stores it as an empty string."""
    store.set_key("null", None)
    assert store.get_key("null") == ""


def test_update_existing_key(store):
    """Test that updating an existing key with a new value works correctly."""
    store.set_key("counter", "1")
    store.set_key("counter", "2")
    assert store.get_key("counter") == "2"


def test_multiple_keys(store):
    """Test that multiple keys can be stored and retrieved independently."""
    store.set_key("a", "1")
    store.set_key("b", "2")
    assert store.get_key("a") == "1"
    assert store.get_key("b") == "2"


def test_different_value_types(store):
    """Test that non-string values are converted to strings when stored."""
    test_cases = [
        (123, "123"),
        (3.14, "3.14"),
        (True, "True"),
        ("", ""),
        ([1, 2, 3], "[1, 2, 3]"),
        ({"key": "value"}, "{'key': 'value'}"),
    ]

    for value, expected in test_cases:
        store.set_key("test", value)
        assert store.get_key("test") == expected


def test_empty_string_value(store):
    """Test that empty string values are stored and retrieved correctly."""
    store.set_key("empty", "")
    assert store.get_key("empty") == ""


def test_overwrite_with_none(store):
    """Test that overwriting a key with None stores it as an empty string."""
    store.set_key("test", "value")
    store.set_key("test", None)
    assert store.get_key("test") == ""
