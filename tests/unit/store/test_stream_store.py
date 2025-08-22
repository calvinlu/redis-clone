"""Unit tests for the StreamStore class."""
import pytest

from app.store.stream_store import StreamStore


class TestStreamStore:
    """Test suite for StreamStore functionality."""

    @pytest.fixture
    def stream_store(self):
        """Create a new StreamStore instance for each test."""
        return StreamStore()

    def test_get_type_returns_stream(self, stream_store):
        """Test that get_type returns 'stream'."""
        assert stream_store.get_type() == "stream"

    def test_xadd_creates_new_stream(self, stream_store):
        """Test adding an entry to a new stream."""
        entry_id = "1-0"
        result = stream_store.xadd(
            "mystream", entry_id, field1="value1", field2="value2"
        )
        assert result == entry_id
        assert len(stream_store.streams["mystream"]) == 1
        assert stream_store.streams["mystream"][0] == {
            "id": entry_id,
            "field1": "value1",
            "field2": "value2",
        }

    def test_xadd_appends_to_existing_stream(self, stream_store):
        """Test adding multiple entries to the same stream."""
        # First entry
        stream_store.xadd("mystream", "1-0", temp=36, humidity=95)

        # Second entry
        entry_id = "1-1"
        result = stream_store.xadd("mystream", entry_id, temp=37, humidity=96)

        assert result == entry_id
        assert len(stream_store.streams["mystream"]) == 2
        assert stream_store.streams["mystream"][1] == {
            "id": entry_id,
            "temp": 37,
            "humidity": 96,
        }

    def test_xadd_multiple_streams(self, stream_store):
        """Test adding entries to multiple different streams."""
        stream_store.xadd("stream1", "1-0", a=1)
        stream_store.xadd("stream2", "1-0", b=2)

        assert len(stream_store.streams) == 2
        assert len(stream_store.streams["stream1"]) == 1
        assert len(stream_store.streams["stream2"]) == 1

    def test_xadd_raises_error_without_fields(self, stream_store):
        """Test that xadd raises ValueError when no field-value pairs are provided."""
        with pytest.raises(ValueError) as excinfo:
            stream_store.xadd("mystream", "1-0")
        assert "wrong number of arguments" in str(excinfo.value)

    def test_flushdb_clears_all_streams(self, stream_store):
        """Test that flushdb removes all streams."""
        stream_store.xadd("stream1", "1-0", a=1)
        stream_store.xadd("stream2", "1-0", b=2)

        stream_store.flushdb()

        assert len(stream_store.streams) == 0

    def test_delete_removes_stream(self, stream_store):
        """Test that delete removes a specific stream."""
        stream_store.xadd("mystream", "1-0", a=1)

        result = stream_store.delete("mystream")

        assert result is True
        assert "mystream" not in stream_store.streams

    def test_delete_nonexistent_stream_returns_false(self, stream_store):
        """Test that delete returns False for non-existent streams."""
        result = stream_store.delete("nonexistent")
        assert result is False
