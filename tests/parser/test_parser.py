import asyncio
import pytest

class MockReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    async def read(self, n):
        if self.pos >= len(self.data):
            return b''
        result = self.data[self.pos:self.pos + n]
        self.pos += n
        return result

    async def readuntil(self, separator):
        if self.pos >= len(self.data):
            raise asyncio.IncompleteReadError(b'', None)
        
        index = self.data.find(separator, self.pos)
        if index == -1:
            raise asyncio.IncompleteReadError(self.data[self.pos:], None)
            
        result = self.data[self.pos:index + len(separator)]
        self.pos = index + len(separator)
        return result
        
    async def readexactly(self, n):
        if self.pos + n > len(self.data):
            raise asyncio.IncompleteReadError(self.data[self.pos:], n)
        result = self.data[self.pos:self.pos + n]
        self.pos += n
        return result

@pytest.mark.asyncio
async def test_parse_ping():
    # PING command in RESP2 format: *1\r\n$4\r\nPING\r\n
    # Create mock data for PING command
    data = b'*1\r\n$4\r\nPING\r\n'
    # Create mock reader with our test data
    reader = MockReader(data)
    
    # Import the parser here to avoid import issues
    from app.parser.parser import RESP2Parser
    
    # Create parser and parse the command
    parser = RESP2Parser(reader)
    result = await parser.parse()
    
    # Verify the result
    assert isinstance(result, list)  # Should be a list
    assert len(result) == 1         # Should have one element
    assert result[0] == b'PING'     # Should be 'PING' in bytes

if __name__ == "__main__":
    # This allows running the test directly: python -m tests.test_parser
    import sys
    import pytest
    sys.exit(pytest.main(["-v", "tests/test_parser.py"]))
