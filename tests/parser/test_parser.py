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


@pytest.mark.asyncio
async def test_parse_ping_command():
    """Test parsing a simple PING command."""
    # PING command in RESP2 format: *1\r\n$4\r\nPING\r\n
    # Create a mock reader with the PING command
    data = b"*1\r\n$4\r\nPING\r\n"
    reader = MockReader(data)
    parser = RESP2Parser(reader)

    # Parse the command
    command, args = await parser.parse_command()

    # Verify the result
    assert command == "PING"
    assert args == []


@pytest.mark.asyncio
async def test_parse_echo_command():
    """Test parsing an ECHO command with an argument."""
    # ECHO command in RESP2 format: *2\r\n$4\r\nECHO\r\n$11\r\nHello World\r\n
    # Create a mock reader with the ECHO command
    data = b"*2\r\n$4\r\nECHO\r\n$11\r\nHello World\r\n"
    reader = MockReader(data)
    parser = RESP2Parser(reader)

    # Parse the command
    command, args = await parser.parse_command()

    # Verify the result
    assert command == "ECHO"
    assert args == ["Hello World"]


@pytest.mark.asyncio
async def test_parse_set_command():
    """Test parsing a SET command with key and value."""
    # SET command in RESP2 format: *3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n
    # Create a mock reader with the SET command
    data = b"*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n"
    reader = MockReader(data)
    parser = RESP2Parser(reader)

    # Parse the command
    command, args = await parser.parse_command()

    # Verify the result
    assert command == "SET"
    assert args == ["key", "value"]


@pytest.mark.asyncio
async def test_parse_case_insensitive_command():
    """Test that command names are case-insensitive."""
    # Command with lowercase name: *1\r\n$4\r\nping\r\n
    # Create a mock reader with the command
    data = b"*1\r\n$4\r\nping\r\n"
    reader = MockReader(data)
    parser = RESP2Parser(reader)

    # Parse the command
    command, args = await parser.parse_command()

    # Verify the result is uppercase
    assert command == "PING"
    assert args == []


@pytest.mark.asyncio
async def test_parse_empty_command():
    """Test parsing an empty command raises an error."""
    # Empty array: *0\r\n
    # Create a mock reader with an empty command
    data = b"*0\r\n"
    reader = MockReader(data)
    parser = RESP2Parser(reader)

    # Parse the command and expect an error
    with pytest.raises(ValueError, match="ERR Protocol error: empty command"):
        await parser.parse_command()


@pytest.mark.asyncio
async def test_parse_invalid_utf8():
    """Test parsing a command with invalid UTF-8 raises an error."""
    # Command with invalid UTF-8: *1\r\n$4\r\n\x80\x81\x82\x83\r\n
    # Create a mock reader with invalid UTF-8 data
    data = b"*1\r\n$4\r\n\x80\x81\x82\x83\r\n"
    reader = MockReader(data)
    parser = RESP2Parser(reader)

    # Parse the command and expect an error
    with pytest.raises(
        ValueError, match="ERR Protocol error: invalid UTF-8 in command"
    ):
        await parser.parse_command()


if __name__ == "__main__":
    # This allows running the test directly: python -m tests.test_parser
    sys.exit(pytest.main(["-v", __file__]))
