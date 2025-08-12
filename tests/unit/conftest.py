"""Fixtures for unit tests."""
import pytest

from app.store import ListStore, Store, StringStore


@pytest.fixture
def store():
    """Create a fresh Store instance for each test."""
    return Store()


@pytest.fixture
def string_store():
    """Create a fresh StringStore instance for each test."""
    return StringStore()


@pytest.fixture
def list_store():
    """Create a fresh ListStore instance for each test."""
    return ListStore()
