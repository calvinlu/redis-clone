"""Unit tests for the RESP2 parser."""

import asyncio
import sys

import pytest

from app.parser.parser import RESP2Parser


class MockReader:
    """Mock implementation of asyncio.StreamReader for testing."""

    def __init__(self, data):
        """Initialize with test data.

        Args:
            data: Bytes to be read by the mock reader
        """
        self.data = data
        self.pos = 0

    async def read(self, n):
        """Read up to n bytes from the mock data.

        Args:
            n: Maximum number of bytes to read

        Returns:
            The bytes read, or an empty bytes object if at end of data
        """
        if self.pos >= len(self.data):
            return b""
        result = self.data[self.pos : self.pos + n]
        self.pos += n
        return result

    async def readuntil(self, separator):
        """Read data until the specified separator is found.

        Args:
            separator: The separator bytes to read until

        Returns:
            The bytes read, including the separator

        Raises:
            asyncio.IncompleteReadError: If the separator is not found in the data
        """
        if self.pos >= len(self.data):
            raise asyncio.IncompleteReadError(b"", None)

        index = self.data.find(separator, self.pos)
        if index == -1:
            raise asyncio.IncompleteReadError(self.data[self.pos :], None)
        result = self.data[self.pos : index + len(separator)]
        self.pos = index + len(separator)
        return result

    async def readexactly(self, n):
        """Read exactly n bytes from the mock data.

        Args:
            n: Number of bytes to read

        Returns:
            The read bytes

        Raises:
            asyncio.IncompleteReadError: If fewer than n bytes are available
        """
        if self.pos + n > len(self.data):
            raise asyncio.IncompleteReadError(self.data[self.pos :], n)
        result = self.data[self.pos : self.pos + n]
        self.pos += n
        return result


@pytest.mark.asyncio
async def test_parse_ping():
    """Test parsing of a PING command in RESP2 format.

    Verifies that the parser correctly parses the PING command and returns
    the expected list structure.
    """
    # PING command in RESP2 format: *1\r\n$4\r\nPING\r\n
    # Create mock data for PING command
    data = b"*1\r\n$4\r\nPING\r\n"
    # Create mock reader with our test data
    reader = MockReader(data)

    # Create parser and parse the command
    parser = RESP2Parser(reader)
    result = await parser.parse()

    # Verify the result
    assert isinstance(result, list)  # Should be a list
    assert len(result) == 1  # Should have one element
    assert result[0] == b"PING"  # Should be 'PING' in bytes (without RESP formatting)


@pytest.mark.asyncio
async def test_parse_echo():
    """Test parsing of an ECHO command in RESP2 format.

    Verifies that the parser correctly parses the ECHO command with its argument
    and returns the expected list structure.
    """
    # ECHO command in RESP2 format: *2\r\n$4\r\nECHO\r\n$5\r\nhello\r\n
    # Create mock data for ECHO command
    data = b"*2\r\n$4\r\nECHO\r\n$5\r\nhello\r\n"
    # Create mock reader with our test data
    reader = MockReader(data)

    # Create parser and parse the command
    parser = RESP2Parser(reader)
    result = await parser.parse()

    # Verify the result
    assert isinstance(result, list)  # Should be a list
    assert len(result) == 2  # Should have two elements
    assert result[0] == b"ECHO"  # First element should be 'ECHO' in bytes
    assert (
        result[1] == b"hello"
    )  # Second element should be the message 'hello' in bytes


if __name__ == "__main__":
    # This allows running the test directly: python -m tests.test_parser
    sys.exit(pytest.main(["-v", __file__]))
