"""Unit tests for the BaseStore class."""
import pytest

from app.store.base import BaseStore


def test_base_store_interface():
    """Test that BaseStore defines the required interface."""
    with pytest.raises(TypeError):
        BaseStore()  # noqa: B024  # Testing abstract class instantiation

    class TestStore(BaseStore):
        def get_type(self) -> str:
            return "test"

        def delete(self, key: str) -> bool:
            return True

    store = TestStore()
    assert store.get_type() == "test"
    assert store.delete("test_key") is True
