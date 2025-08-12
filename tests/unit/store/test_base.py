"""Unit tests for the BaseStore class."""
import pytest

from app.store.base import BaseStore


def test_base_store_interface():
    """Test that BaseStore defines the required interface."""
    with pytest.raises(TypeError):
        BaseStore()  # Can't instantiate abstract class

    class TestStore(BaseStore):
        def get_type(self):
            return "test"

        def delete(self, key):
            return True

    store = TestStore()
    assert store.get_type() == "test"
    assert store.delete("test_key") is True
