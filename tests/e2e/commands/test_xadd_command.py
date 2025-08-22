"""End-to-end tests for the Redis XADD command."""
import pytest

from tests.e2e.base_e2e_test import BaseE2ETest


class TestXAddCommandE2E(BaseE2ETest):
    """End-to-end tests for the XADD command."""

    @pytest.mark.asyncio
    async def test_xadd_creates_new_stream(self):
        """Test that XADD creates a new stream and returns the entry ID."""
        # Test XADD command
        result = await self._test_client.execute_command(
            "XADD", "mystream", "0-1", "temperature", "36"
        )
        assert result == "0-1"

        # Verify the type is set to 'stream'
        type_result = await self._test_client.execute_command("TYPE", "mystream")
        assert type_result == "stream"

    @pytest.mark.asyncio
    async def test_xadd_with_multiple_field_value_pairs(self):
        """Test XADD with multiple field-value pairs."""
        result = await self._test_client.execute_command(
            "XADD", "weather", "1526919030474-0", "temperature", "36", "humidity", "95"
        )
        assert result == "1526919030474-0"

        # Verify the type is set to 'stream'
        type_result = await self._test_client.execute_command("TYPE", "weather")
        assert type_result == "stream"

    @pytest.mark.asyncio
    async def test_xadd_error_cases(self):
        """Test XADD error cases."""
        # Test with odd number of arguments (missing value for field)
        with pytest.raises(Exception) as exc_info:
            await self._test_client.execute_command(
                "XADD", "mystream", "0-1", "temperature"
            )
        assert "wrong number of arguments" in str(exc_info.value).lower()

        # Test with missing entry ID
        with pytest.raises(Exception) as exc_info:
            await self._test_client.execute_command("XADD", "mystream")
        assert "wrong number of arguments" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_xadd_followed_by_type_command(self):
        """Test XADD followed by TYPE command returns 'stream'."""
        # This is the exact test case mentioned in the requirements
        await self._test_client.execute_command(
            "XADD", "stream_key", "0-1", "foo", "bar"
        )
        type_result = await self._test_client.execute_command("TYPE", "stream_key")
        assert type_result == "stream"
