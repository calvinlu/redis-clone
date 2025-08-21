"""Redis RESP2 Protocol Parser.

This module implements a parser for the Redis Serialization Protocol (RESP2). It can
parse RESP2 messages into Python native types and encode Python values into RESP2 format.

The parser supports all RESP2 data types:
    - Simple Strings
    - Errors
    - Integers
    - Bulk Strings
    - Arrays
"""
import asyncio
from typing import List, Optional, Union

# Type aliases
RESPValue = Union[str, int, bytes, List[bytes], None]
CRLF = b"\r\n"


class RESP2Parser:
    """Parser for Redis RESP2 protocol.

    This class provides methods to parse RESP2 protocol messages from an asyncio stream.
    It handles all RESP2 data types and converts them to appropriate Python types.

    Args:
        reader: An asyncio.StreamReader instance to read data from.
    """

    def __init__(self, reader: asyncio.StreamReader) -> None:
        """Initialize the RESP2 parser with a stream reader.

        Args:
            reader: An asyncio.StreamReader instance to read data from.
        """
        self.reader = reader

    async def read_line(self) -> bytes:
        """Read a line ending with CRLF.

        Returns:
            The line read from the stream, with CRLF removed.

        Raises:
            asyncio.IncompleteReadError: If the connection is closed before CRLF is found.
        """
        line = await self.reader.readuntil(CRLF)
        return line[:-2]  # Remove CRLF

    async def parse_command(self) -> tuple[str, list[str]]:
        """Parse and validate a Redis command from the stream.

        Returns:
            tuple[str, list[str]]: A tuple of (command_name, args) where command_name is uppercase.

        Raises:
            ConnectionError: If the connection is closed by the client.
            ValueError: If the command structure is invalid.
            asyncio.IncompleteReadError: If the connection is closed unexpectedly.
        """
        value = await self.parse()

        # Command must be an array of bulk strings
        if not isinstance(value, list):
            raise ValueError("ERR Protocol error: expected array")

        if not value:
            raise ValueError("ERR Protocol error: empty command")

        # Convert all elements to strings
        try:
            command_parts = []
            for item in value:
                if isinstance(item, bytes):
                    command_parts.append(item.decode("utf-8"))
                elif isinstance(item, str):
                    command_parts.append(item)
                else:
                    raise ValueError("ERR Protocol error: invalid command format")

            if not command_parts:
                raise ValueError("ERR Protocol error: empty command")

            # First part is the command name (case-insensitive in Redis)
            command_name = command_parts[0].upper()
            args = command_parts[1:]

            return command_name, args

        except UnicodeDecodeError as e:
            raise ValueError("ERR Protocol error: invalid UTF-8 in command") from e

    async def parse(self) -> RESPValue:
        """Parse the next value from the stream.

        Returns:
            The parsed value, which can be a string, int, bytes, list, or None.

        Raises:
            ConnectionError: If the connection is closed by the client.
            ValueError: If an unknown RESP2 data type is encountered.
            asyncio.IncompleteReadError: If the connection is closed unexpectedly.
        """
        data_type = await self.reader.read(1)
        if not data_type:
            raise ConnectionError("Connection closed by client")

        if data_type == b"+":  # Simple String
            return await self._parse_simple_string()
        elif data_type == b"-":  # Error
            return await self._parse_error()
        elif data_type == b":":  # Integer
            return await self._parse_integer()
        elif data_type == b"$":  # Bulk String
            return await self._parse_bulk_string()
        elif data_type == b"*":  # Array
            return await self._parse_array()
        else:
            raise ValueError(f"Unknown RESP data type: {data_type}")

    async def _parse_simple_string(self) -> str:
        """Parse a simple string.

        Returns:
            str: The decoded string.

        Raises:
            UnicodeDecodeError: If the string cannot be decoded as UTF-8.
        """
        line = await self.read_line()
        try:
            return line.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid UTF-8 in simple string: {line!r}") from e

    async def _parse_error(self) -> str:
        """Parse an error message.

        Returns:
            str: The error message prefixed with 'Error: '.

        Raises:
            UnicodeDecodeError: If the error message cannot be decoded as UTF-8.
        """
        line = await self.read_line()
        try:
            return f"Error: {line.decode('utf-8')}"
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid UTF-8 in error message: {line!r}") from e

    async def _parse_integer(self) -> int:
        """Parse an integer.

        Returns:
            int: The parsed integer value.

        Raises:
            ValueError: If the input cannot be converted to an integer.
        """
        line = await self.read_line()
        try:
            return int(line)
        except ValueError as e:
            raise ValueError(f"Invalid integer: {line}") from e

    async def _parse_bulk_string(self) -> Optional[bytes]:
        """Parse a bulk string.

        Returns:
            Optional[bytes]: The binary data of the bulk string, or None for null bulk string.

        Raises:
            ValueError: If the length is invalid or the data cannot be read.
            asyncio.IncompleteReadError: If the connection is closed unexpectedly.
        """
        length_line = await self.read_line()
        try:
            length = int(length_line)
        except ValueError as e:
            raise ValueError(f"Invalid bulk string length: {length_line}") from e
        if length == -1:  # Null bulk string
            return None
        data = await self.reader.readexactly(length)
        # Read the trailing CRLF
        await self.reader.readexactly(2)
        return data

    async def _parse_array(self) -> List[RESPValue]:
        """Parse an array of RESP values.

        Returns:
            List[RESPValue]: A list of parsed RESP values.

        Raises:
            ValueError: If the array length is invalid.
            asyncio.IncompleteReadError: If the connection is closed unexpectedly.
        """
        length_line = await self.read_line()
        try:
            length = int(length_line)
        except ValueError as e:
            raise ValueError(f"Invalid array length: {length_line}") from e
        if length == -1:  # Null array
            return []
        return [await self.parse() for _ in range(length)]


# Special marker for null arrays in RESP
class NullArray:
    """Special marker class for null arrays in RESP2 protocol."""

    def __str__(self):
        return "*-1"


def encode(
    value: Union[
        str, int, bytes, List[Union[str, bytes, int, None, NullArray]], None, NullArray
    ]
) -> bytes:
    """Encode a Python value to RESP2 format.

    This function converts Python native types to their RESP2 protocol representation.
    It handles strings, integers, bytes, lists, None values, and NullArray.

    Args:
        value: The value to encode. Can be str, int, bytes, list, None, or NullArray.

    Returns:
        bytes: The RESP2-encoded representation of the value.

    Raises:
        ValueError: If the value type is not supported for RESP2 encoding.
        UnicodeEncodeError: If a string cannot be encoded to UTF-8.

    Examples:
        >>> encode("OK")
        b'+OK\r\n'
        >>> encode(42)
        b':42\r\n'
        >>> encode(b'hello')
        b'$5\r\nhello\r\n'
        >>> encode(["SET", "key", "value"])
        b'*3\r\n+SET\r\n+key\r\n+value\r\n'
        >>> encode(None)
        b'$-1\r\n'
        >>> encode(NullArray())
        b'*-1\r\n'
    """
    if isinstance(value, NullArray):
        return b"*-1\r\n"  # Null array

    if value is None:
        return b"$-1\r\n"  # Null bulk string

    if isinstance(value, str):
        # Simple string
        return f"+{value}\r\n".encode("utf-8")
    if isinstance(value, int):
        # Integer
        return f":{value}\r\n".encode("utf-8")
    if isinstance(value, bytes):
        # Bulk string
        return b"$" + str(len(value)).encode("utf-8") + b"\r\n" + value + b"\r\n"
    if isinstance(value, list):
        # Array
        result = [f"*{len(value)}\r\n".encode("utf-8")]
        for item in value:
            if isinstance(item, str):
                item = item.encode("utf-8")
            result.append(encode(item))
        return b"".join(result)
    raise ValueError(f"Unsupported type for RESP2 encoding: {type(value)}")
