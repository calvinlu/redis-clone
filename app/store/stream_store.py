"""Redis Stream data type implementation.

This module provides the StreamStore class which implements Redis Stream functionality.
Streams are append-only data structures that store entries with unique IDs and
field-value pairs. This implementation supports basic stream operations including
XADD for adding new entries to a stream.

The stream data is stored in memory using a dictionary where each key maps to a
list of entries. Each entry is a dictionary containing an 'id' field and the
provided field-value pairs.
"""
import re
from typing import Any, Dict, List, Tuple

from .base import BaseStore


class StreamStore(BaseStore):
    """Handles storage of stream data structures with entries containing field-value pairs."""

    def __init__(self):
        """Initialize a new StreamStore with an empty dictionary for streams."""
        self.streams: Dict[str, List[Dict[str, Any]]] = {}

    def get_type(self) -> str:
        """Return the type name of this store."""
        return "stream"

    def _parse_entry_id(self, entry_id: str) -> Tuple[int, int]:
        """Parse and validate a stream entry ID.

        Args:
            entry_id: The entry ID string in format "TIMESTAMP-SEQUENCE" or "TIMESTAMP-*"

        Returns:
            A tuple of (timestamp, sequence) as integers. For auto-sequence case, sequence will be -1.

        Raises:
            ValueError: If the entry ID is invalid
        """
        if not entry_id or not isinstance(entry_id, str):
            raise ValueError("ERR Invalid stream ID specified")

        # Check format - allow * for sequence number or standalone *
        if not re.match(r"^\d+-\d+$|^\d+-\*$|^\*$", entry_id):
            raise ValueError("ERR Invalid stream ID specified")

        if entry_id == "*":
            return -1, -1

        try:
            timestamp_str, sequence_str = entry_id.split("-")
            timestamp = int(timestamp_str)

            # Handle auto-sequence case
            if sequence_str == "*":
                return timestamp, -1  # Special value to indicate auto-sequence

            sequence = int(sequence_str)
        except (ValueError, AttributeError) as e:
            raise ValueError("ERR Invalid stream ID specified") from e

        # Validate numbers are non-negative and within 64-bit range
        if timestamp < 0 or sequence < 0:
            raise ValueError("ERR The ID specified in XADD must be greater than 0-0")

        # Special case: 0-0 is not allowed
        if timestamp == 0 and sequence == 0:
            raise ValueError("ERR The ID specified in XADD must be greater than 0-0")

        # Check 64-bit upper bound
        if timestamp > 2**64 - 1 or sequence > 2**64 - 1:
            raise ValueError("ERR The ID specified in XADD is not a valid stream ID")

        return timestamp, sequence

    def _validate_entry_id_order(
        self, key: str, new_timestamp: int, new_sequence: int
    ) -> None:
        """Validate that the new entry ID is greater than the last entry's ID.

        Args:
            key: The stream key
            new_timestamp: The timestamp of the new entry
            new_sequence: The sequence number of the new entry

        Raises:
            ValueError: If the new ID is not greater than the last entry's ID
        """
        if key not in self.streams or not self.streams[key]:
            return

        last_entry = self.streams[key][-1]
        last_timestamp, last_sequence = self._parse_entry_id(last_entry["id"])

        # Compare timestamps first
        if new_timestamp < last_timestamp:
            raise ValueError(
                "ERR The ID specified in XADD is equal or smaller than the target stream top item"
            )
        if new_timestamp == last_timestamp and new_sequence <= last_sequence:
            # Only validate sequence if timestamps are equal
            raise ValueError(
                "ERR The ID specified in XADD is equal or smaller than the target stream top item"
            )

    def xadd(self, key: str, entry_id: str, **field_value_pairs: str) -> str:
        """Add an entry to a stream.

        Args:
            key: The stream key
            entry_id: The ID for the new entry in format "TIMESTAMP-SEQUENCE" or "TIMESTAMP-*"
            **field_value_pairs: Field-value pairs to store in the entry

        Returns:
            The entry ID that was added

        Raises:
            ValueError: If no field-value pairs are provided or if entry_id is invalid
        """
        if not field_value_pairs:
            raise ValueError("ERR wrong number of arguments for 'xadd' command")

        # Parse the entry ID (may contain * for auto-sequence)
        try:
            timestamp, sequence = self._parse_entry_id(entry_id)
        except ValueError as e:
            raise ValueError(str(e)) from e

        # Handle auto-sequence
        if sequence == -1:  # This is our special value for auto-sequence
            sequence = self._get_next_sequence(key, timestamp)
            entry_id = f"{timestamp}-{sequence}"

        # Validate the entry ID is greater than the last entry's ID
        self._validate_entry_id_order(key, timestamp, sequence)

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

    def _get_next_sequence(self, key: str, timestamp: int) -> int:
        """Get the next sequence number for a given timestamp.

        Args:
            key: The stream key
            timestamp: The timestamp to get the next sequence for

        Returns:
            The next sequence number (0 for new timestamp, or last_sequence + 1)
        """
        if key not in self.streams or not self.streams[key]:
            # Special case: if timestamp is 0, start sequence at 1
            return 1 if timestamp == 0 else 0

        last_entry = self.streams[key][-1]
        last_timestamp, last_sequence = self._parse_entry_id(last_entry["id"])

        if timestamp > last_timestamp:
            # New timestamp, reset sequence to 0 (or 1 if timestamp is 0)
            return 1 if timestamp == 0 else 0
        elif timestamp == last_timestamp:
            # Same timestamp, increment sequence
            return last_sequence + 1
        else:
            # This should not happen due to _validate_entry_id_order
            raise ValueError(
                "ERR The ID specified in XADD is equal or smaller than the target stream top item"
            )
