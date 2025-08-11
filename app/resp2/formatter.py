"""RESP2 response formatter.

This module provides functions to convert Python types into RESP2 protocol format.
"""
from typing import Any, List, Union, ByteString, Optional


def format_response(response: Union[str, int, List[Any], bytes, None]) -> bytes:
    """Convert Python types to RESP2 formatted bytes.
    
    Args:
        response: The Python value to convert to RESP2 format.
                 Can be str, int, list, bytes, or None.
                 
    Returns:
        RESP2 formatted bytes ready to be sent over the wire.
        
    Examples:
        >>> format_response("OK")
        b'+OK\r\n'
        >>> format_response(42)
        b':42\r\n'
        >>> format_response([b"foo", b"bar"])
        b'*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n'
        >>> format_response(None)
        b'$-1\r\n'
    Raises:
        ValueError: If the response type is not supported
    """
    if response is None:
        return b"$-1\r\n"  # Null bulk string
    elif isinstance(response, str):
        return f"+{response}\r\n".encode('utf-8')
    elif isinstance(response, (bytes, bytearray)):
        return b'$' + str(len(response)).encode() + b'\r\n' + response + b'\r\n'
    elif isinstance(response, int):
        return f":{response}\r\n".encode('utf-8')
    elif isinstance(response, (list, tuple)):
        # Recursively format array elements
        result = [f"*{len(response)}\r\n".encode('utf-8')]
        for item in response:
            result.append(format_response(item))
        return b''.join(result)
    else:
        raise ValueError(f"Unsupported response type: {type(response)}")


def format_error(message: str) -> bytes:
    """Format an error message in RESP2 format.
    
    Args:
        message: The error message to format
        
    Returns:
        RESP2 formatted error message
    """
    return f"-{message}\r\n".encode('utf-8')


def format_pipeline(responses: List[Any]) -> bytes:
    """Format multiple responses for pipelining.
    
    Args:
        responses: List of response objects to format
        
    Returns:
        RESP2 formatted bytes with all responses concatenated
    """
    return b''.join(format_response(r) for r in responses)
