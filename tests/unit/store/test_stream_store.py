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
        assert (
            str(exc_info.value)
            == "ERR The ID specified in XADD is equal or smaller than the target stream top item"
        )

    def test_xadd_smaller_timestamp(self, store):
        """Test adding an entry with a smaller timestamp."""
        store.xadd("mystream", "2-0", f1="v1")

        with pytest.raises(ValueError) as exc_info:
            store.xadd("mystream", "1-0", f2="v2")
        assert (
            str(exc_info.value)
            == "ERR The ID specified in XADD is equal or smaller than the target stream top item"
        )

    def test_xadd_same_timestamp_smaller_sequence(self, store):
        """Test adding an entry with the same timestamp but smaller sequence number."""
        store.xadd("mystream", "1-1", f1="v1")  # Higher sequence first

        with pytest.raises(ValueError) as exc_info:
            store.xadd("mystream", "1-0", f2="v2")
        assert (
            str(exc_info.value)
            == "ERR The ID specified in XADD is equal or smaller than the target stream top item"
        )

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

    def test_xadd_auto_sequence_new_stream(self, store):
        """Test auto-sequence with * in a new stream."""
        # First entry with auto-sequence
        result = store.xadd("mystream", "1-*", field1="value1")
        assert result == "1-0"  # Should start with sequence 0
        assert store.streams["mystream"][0]["id"] == "1-0"

        # Second entry with same timestamp, auto-sequence should increment
        result = store.xadd("mystream", "1-*", field2="value2")
        assert result == "1-1"
        assert store.streams["mystream"][1]["id"] == "1-1"

    def test_xadd_auto_sequence_timestamp_zero(self, store):
        """Test auto-sequence with timestamp 0."""
        # Timestamp 0 should start sequence at 1 (special case)
        result = store.xadd("mystream", "0-*", field1="value1")
        assert result == "0-1"
        assert store.streams["mystream"][0]["id"] == "0-1"

        # Next auto-sequence with same timestamp
        result = store.xadd("mystream", "0-*", field2="value2")
        assert result == "0-2"

    def test_xadd_mixed_auto_and_manual_sequence(self, store):
        """Test mixing auto and manual sequence numbers."""
        # Add with manual sequence
        store.xadd("mystream", "1-5", field1="value1")

        # Add with auto-sequence, should use next sequence number (6)
        result = store.xadd("mystream", "1-*", field2="value2")
        assert result == "1-6"

        # Add with higher timestamp, auto-sequence should reset
        result = store.xadd("mystream", "2-*", field3="value3")
        assert result == "2-0"

    def test_xadd_auto_sequence_after_deletion(self, store):
        """Test auto-sequence works correctly after stream is deleted."""
        # Add some entries
        store.xadd("mystream", "1-*", f1="v1")
        store.xadd("mystream", "1-*", f2="v2")  # 1-1

        # Delete the stream
        store.delete("mystream")

        # Add to stream again, should start fresh
        result = store.xadd("mystream", "2-*", f3="v3")
        assert result == "2-0"
        assert len(store.streams["mystream"]) == 1

    def test_xadd_large_timestamp(self, store):
        """Test with a large but valid timestamp (2^53-1 is the max safe integer in JavaScript)."""
        large_ts = str(2**53 - 1)
        result = store.xadd("mystream", f"{large_ts}-*", field="value")
        assert result == f"{large_ts}-0"

    def test_xadd_large_sequence_number(self, store):
        """Test with a large sequence number (2^53-1)."""
        # First add an entry with a small timestamp
        store.xadd("mystream", "1-*", f0="v0")

        # Now test with a large sequence number
        large_seq = str(2**53 - 1)
        result = store.xadd("mystream", f"1-{large_seq}", f1="v1")
        assert result == f"1-{large_seq}"

        # Next auto-sequence should increment the sequence number
        result = store.xadd("mystream", "1-*", f2="v2")
        assert result == "1-9007199254740992"  # 2^53
