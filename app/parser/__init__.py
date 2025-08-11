"""RESP2 Protocol Parser.

This package provides functionality to parse Redis Serialization Protocol (RESP2) messages.
It includes a parser that can handle various RESP2 data types and convert them to
Python native types.

Main components:
    - RESP2Parser: The main parser class that handles RESP2 protocol messages
"""

from app.parser.parser import RESP2Parser  # noqa: F401

__all__ = ["RESP2Parser"]
