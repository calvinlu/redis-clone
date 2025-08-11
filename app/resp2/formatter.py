"""RESP2 response formatter.

This module provides functions to convert Python types into RESP2 protocol format.
It handles the serialization of Python types to the Redis Serialization Protocol (RESP2).
"""
from typing import Any, Iterable, List, Union

RESPValue = Union[str, int, List[Any], bytes, bytearray, None]


def format_response(response: RESPValue) -> bytes:
    """Convert Python types to RESP2 formatted bytes.

    This function serializes Python values to the RESP2 protocol format used by Redis.
    It supports strings, integers, bytes, lists, and None values.

    Args:
        response: The Python value to convert to RESP2 format.
                 Can be str, int, list, bytes, bytearray, or None.

    Returns:
        RESP2 formatted bytes ready to be sent over the wire.

    Raises:
        ValueError: If the response type is not supported for RESP2 encoding.
        UnicodeEncodeError: If a string cannot be encoded as UTF-8.

    Examples:
        >>> format_response("OK")
        b'+OK\r\n'
        >>> format_response(42)
        b':42\r\n'
        >>> format_response([b"foo", b"bar"])
        b'*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n'
        >>> format_response(None)
        b'$-1\r\n'
    Note:
        - Strings are encoded as simple strings (starts with '+').
        - Integers are encoded as integers (starts with ':').
        - Bytes/bytearrays are encoded as bulk strings (starts with '$').
        - Lists/tuples are encoded as arrays (starts with '*').
        - None is encoded as a null bulk string ('$-1\r\n').
    """
    if response is None:
        return b"$-1\r\n"  # Null bulk string

    if isinstance(response, str):
        # Simple string
        return f"+{response}\r\n".encode("utf-8")

    if isinstance(response, (bytes, bytearray)):
        # Bulk string
        return b"$" + str(len(response)).encode("utf-8") + b"\r\n" + response + b"\r\n"
    if isinstance(response, int):
        # Integer
        return f":{response}\r\n".encode("utf-8")

    if isinstance(response, (list, tuple)):
        # Array - recursively format each element
        result = [f"*{len(response)}\r\n".encode("utf-8")]
        for item in response:
            result.append(format_response(item))
        return b"".join(result)

    raise ValueError(f"Unsupported response type: {type(response)}")


def format_error(message: str) -> bytes:
    """Format an error message in RESP2 format.

    Args:
        message: The error message to format. Will be encoded as UTF-8.

    Returns:
        RESP2 formatted error message (starts with '-').

    Raises:
        UnicodeEncodeError: If the message cannot be encoded as UTF-8.

    Example:
        >>> format_error("ERR unknown command 'FOO'")
        b"-ERR unknown command 'FOO'\r\n"
    """
    return f"-{message}\r\n".encode("utf-8")


def format_pipeline(responses: Iterable[RESPValue]) -> bytes:
    """Format multiple responses for pipelining.

    This function formats multiple responses into a single byte string,
    which is useful for Redis pipelining where multiple commands are
    sent at once and multiple responses are expected.

    Args:
        responses: An iterable of response objects to format.
                  Each response can be any type supported by format_response().

    Returns:
        RESP2 formatted bytes with all responses concatenated together.

    Example:
        >>> format_pipeline(["PONG", 42, None])
        b'+PONG\r\n:42\r\n$-1\r\n'
    Note:
        This is different from an array of responses. Each response is
        formatted independently and concatenated together.
    """
    return b"".join(format_response(response) for response in responses)
