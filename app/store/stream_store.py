"""Redis Stream data type implementation.

This module provides the StreamStore class which implements Redis Stream functionality.
Streams are append-only data structures that store entries with unique IDs and
field-value pairs. This implementation supports basic stream operations including
XADD for adding new entries to a stream.

The stream data is stored in memory using a dictionary where each key maps to a
list of entries. Each entry is a dictionary containing an 'id' field and the
provided field-value pairs.
"""
from typing import Any, Dict, List

from .base import BaseStore


class StreamStore(BaseStore):
    """Handles storage of stream data structures with entries containing field-value pairs."""

    def __init__(self):
        """Initialize a new StreamStore with an empty dictionary for streams."""
        self.streams: Dict[str, List[Dict[str, Any]]] = {}

    def get_type(self) -> str:
        """Return the type name of this store."""
        return "stream"

    def xadd(self, key: str, entry_id: str, **field_value_pairs: str) -> str:
        """Add an entry to a stream.

        Args:
            key: The stream key
            entry_id: The ID for the new entry
            **field_value_pairs: Field-value pairs to store in the entry

        Returns:
            The entry ID that was added

        Raises:
            ValueError: If no field-value pairs are provided
        """
        if not field_value_pairs:
            raise ValueError("ERR wrong number of arguments for 'xadd' command")

        entry = {"id": entry_id, **field_value_pairs}

        if key not in self.streams:
            self.streams[key] = []

        self.streams[key].append(entry)
        return entry_id

    def delete(self, key: str) -> bool:
        existed = key in self.streams
        self.streams.pop(key, None)
        return existed

    def flushdb(self) -> None:
        self.streams.clear()
