"""Integration tests for the Redis XADD command."""
import pytest

from app.store import Store


class TestXAddCommandIntegration:
    """Integration tests for the XADD command with Store."""

    @pytest.mark.asyncio
    async def test_xadd_creates_new_stream(self):
        """Test that XADD creates a new stream when it doesn't exist."""
        store = Store()
        result = await store.xadd("mystream", "0-1", "temperature", "36")

        assert result == "0-1"
        assert "mystream" in store.key_types
        assert store.key_types["mystream"] == "stream"

    @pytest.mark.asyncio
    async def test_xadd_appends_to_existing_stream(self):
        """Test that XADD appends to an existing stream."""
        store = Store()
        # First entry
        result1 = await store.xadd("mystream", "0-1", "temperature", "36")
        # Second entry
        result2 = await store.xadd("mystream", "0-2", "temperature", "37")

        assert result1 == "0-1"
        assert result2 == "0-2"
        assert len(store.streams.get("mystream", [])) == 2

    @pytest.mark.asyncio
    async def test_xadd_with_multiple_field_value_pairs(self):
        """Test that XADD handles multiple field-value pairs."""
        store = Store()
        result = await store.xadd(
            "mystream", "0-1", "temperature", "36", "humidity", "95", "pressure", "1013"
        )

        assert result == "0-1"
        stream = store.streams.get("mystream")
        assert stream is not None
        entry = next((e for e in stream if e["id"] == "0-1"), None)
        assert entry is not None
        assert entry["temperature"] == "36"
        assert entry["humidity"] == "95"
        assert entry["pressure"] == "1013"
