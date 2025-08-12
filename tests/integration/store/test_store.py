"""Unit tests for the Store class."""

import time
from unittest.mock import patch

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


def test_set_with_ttl_before_expiry(store):
    """Test that sets a key with an expiry and gets before expiration"""
    store.set_key("test", "value", 10)
    assert store.get_key("test") == "value"


def test_set_with_ttl_after_expiry(store):
    """Test that sets a key with an expiry and gets after expiration"""
    with patch("time.time") as mock_time:
        mock_time.return_value = 1000.0
        store.set_key("test", "value", 10)
        mock_time.return_value = 1000.02
        assert store.get_key("test") is None


def test_set_with_neg_expiry(store):
    """Test that sets a key with a negative expiration"""
    with pytest.raises(ValueError, match="ERR invalid expire time set"):
        store.set_key("test", "value", -10)
