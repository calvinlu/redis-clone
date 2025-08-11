"""
Redis RESP2 Protocol Parser
Handles parsing of RESP2 protocol messages.
"""
import asyncio
from typing import Union, List, Optional

# Type aliases
RESPValue = Union[str, int, bytes, List[bytes], None]
CRLF = b'\r\n'

class RESP2Parser:
    """Parser for Redis RESP2 protocol."""
    
    def __init__(self, reader: asyncio.StreamReader):
        self.reader = reader
    
    async def read_line(self) -> bytes:
        """Read a line ending with CRLF."""
        line = await self.reader.readuntil(CRLF)
        return line[:-2]  # Remove CRLF
    
    async def parse(self) -> RESPValue:
        """Parse the next value from the stream."""
        data_type = await self.reader.read(1)
        if not data_type:
            raise ConnectionError("Connection closed by client")
            
        if data_type == b'+':  # Simple String
            return await self._parse_simple_string()
        elif data_type == b'-':  # Error
            return await self._parse_error()
        elif data_type == b':':  # Integer
            return await self._parse_integer()
        elif data_type == b'$':  # Bulk String
            return await self._parse_bulk_string()
        elif data_type == b'*':  # Array
            return await self._parse_array()
        else:
            raise ValueError(f"Unknown RESP data type: {data_type}")
    
    async def _parse_simple_string(self) -> str:
        """Parse a simple string."""
        line = await self.read_line()
        return line.decode('utf-8')
    
    async def _parse_error(self) -> str:
        """Parse an error message."""
        line = await self.read_line()
        return f"Error: {line.decode('utf-8')}"
    
    async def _parse_integer(self) -> int:
        """Parse an integer."""
        line = await self.read_line()
        try:
            return int(line)
        except ValueError:
            raise ValueError(f"Invalid integer: {line}")
    
    async def _parse_bulk_string(self) -> Optional[bytes]:
        """Parse a bulk string."""
        length_line = await self.read_line()
        try:
            length = int(length_line)
        except ValueError:
            raise ValueError(f"Invalid bulk string length: {length_line}")
        
        if length == -1:  # Null bulk string
            return None
            
        data = await self.reader.readexactly(length)
        # Read the trailing CRLF
        await self.reader.readexactly(2)
        return data
    
    async def _parse_array(self) -> List[RESPValue]:
        """Parse an array of RESP values."""
        length_line = await self.read_line()
        try:
            length = int(length_line)
        except ValueError:
            raise ValueError(f"Invalid array length: {length_line}")
        
        if length == -1:  # Null array
            return []
            
        return [await self.parse() for _ in range(length)]

# Helper function to encode RESP2 values
def encode(value: Union[str, int, bytes, List[Union[str, bytes]]]) -> bytes:
    """Encode a Python value to RESP2 format."""
    if value is None:
        return b'$-1\r\n'
    elif isinstance(value, str):
        return f"+{value}\r\n".encode('utf-8')
    elif isinstance(value, int):
        return f":{value}\r\n".encode('utf-8')
    elif isinstance(value, bytes):
        return b'$' + str(len(value)).encode('utf-8') + b'\r\n' + value + b'\r\n'
    elif isinstance(value, list):
        result = [f"*{len(value)}\r\n".encode('utf-8')]
        for item in value:
            if isinstance(item, str):
                item = item.encode('utf-8')
            result.append(encode(item))
        return b''.join(result)
    else:
        raise ValueError(f"Unsupported type for RESP2 encoding: {type(value)}")