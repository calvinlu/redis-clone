"""Unit tests for the StreamStore class with entry ID validation."""
import pytest

from app.store.stream_store import StreamStore


class TestStreamStore:
    """Test cases for the StreamStore class."""

    @pytest.fixture
    def store(self):
        """Create a StreamStore instance for testing."""
        return StreamStore()

    def test_xadd_valid_entry(self, store):
        """Test adding a valid entry to a new stream."""
        result = store.xadd("mystream", "1-0", field1="value1")
        assert result == "1-0"
        assert len(store.streams.get("mystream", [])) == 1
        assert store.streams["mystream"][0]["id"] == "1-0"
        assert store.streams["mystream"][0]["field1"] == "value1"

    def test_xadd_multiple_entries(self, store):
        """Test adding multiple entries with increasing IDs."""
        store.xadd("mystream", "1-0", f1="v1")
        store.xadd("mystream", "1-1", f2="v2")  # Same timestamp, higher seq
        store.xadd("mystream", "2-0", f3="v3")  # Higher timestamp

        stream = store.streams["mystream"]
        assert len(stream) == 3
        assert [entry["id"] for entry in stream] == ["1-0", "1-1", "2-0"]

    def test_xadd_invalid_entry_id_format(self, store):
        """Test adding entries with invalid ID formats."""
        invalid_ids = ["", "not-an-id", "1-", "-1", "1-2-3", "a-1", "1-b", "0-0"]

        for entry_id in invalid_ids:
            with pytest.raises(ValueError):
                store.xadd("mystream", entry_id, field="value")

    def test_xadd_duplicate_entry_id(self, store):
        """Test adding an entry with a duplicate ID."""
        store.xadd("mystream", "1-0", f1="v1")

        with pytest.raises(ValueError) as exc_info:
            store.xadd("mystream", "1-0", f2="v2")
        assert "equal or smaller" in str(exc_info.value).lower()

    def test_xadd_smaller_timestamp(self, store):
        """Test adding an entry with a smaller timestamp."""
        store.xadd("mystream", "2-0", f1="v1")

        with pytest.raises(ValueError) as exc_info:
            store.xadd("mystream", "1-0", f2="v2")
        assert "equal or smaller" in str(exc_info.value).lower()

    def test_xadd_same_timestamp_smaller_sequence(self, store):
        """Test adding an entry with the same timestamp but smaller sequence number."""
        store.xadd("mystream", "1-1", f1="v1")  # Higher sequence first

        with pytest.raises(ValueError) as exc_info:
            store.xadd("mystream", "1-0", f2="v2")
        assert "equal or smaller" in str(exc_info.value).lower()

    def test_xadd_large_numbers(self, store):
        """Test adding entries with very large numbers in IDs."""
        large_num = str(2**64)  # One more than max 64-bit unsigned int
        invalid_ids = [f"{large_num}-0", f"0-{large_num}", f"{large_num}-{large_num}"]

        for entry_id in invalid_ids:
            with pytest.raises(ValueError) as exc_info:
                store.xadd("mystream", entry_id, field="value")
            assert "not a valid stream ID" in str(exc_info.value)

    def test_xadd_field_value_pairs(self, store):
        """Test that field-value pairs are stored correctly."""
        # Test with multiple field-value pairs
        store.xadd("mystream", "1-0", f1="v1", f2="v2", f3="v3")

        entry = store.streams["mystream"][0]
        assert entry == {"id": "1-0", "f1": "v1", "f2": "v2", "f3": "v3"}
