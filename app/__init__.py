"""Redis Server Implementation in Python.

This package provides a Redis-compatible server implementation using Python and asyncio.
It supports a subset of Redis commands and follows the RESP (REdis Serialization Protocol) v2.

Modules:
    - commands: Package containing implementations of various Redis commands
    - connection: Handles client connections and command dispatching
    - parser: Implements the RESP2 protocol parser
    - resp2: RESP2 protocol formatters and utilities
    - store: Key-value store implementation
"""

__version__ = "0.1.0"
__author__ = "Your Name <your.email@example.com>"

# This makes the package importable and provides version information
