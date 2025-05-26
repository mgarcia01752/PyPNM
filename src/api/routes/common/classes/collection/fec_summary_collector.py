# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Any, Dict, List
from pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary

class FecSummaryCollector:
    """
    Dynamic in-memory store for FEC summary data per DOCSIS channel.

    Initialized directly from a CmDsOfdmFecSummary service object.
    Internal structure:
        _data: Dict[profile_id, Dict[timestamp, Dict[str, Any]]]
    """
    def __init__(self, summary_service: CmDsOfdmFecSummary):
        """
        Construct collector from a FEC summary service instance.

        Args:
            summary_service: an instance of CmDsOfdmFecSummary
        """
        summary = summary_service.to_dict()
        self.channel_id = summary.get('channel_id')
        if self.channel_id is None:
            raise ValueError("FEC summary missing 'channel_id'")
        self._data: Dict[int, Dict[int, Dict[str, Any]]] = {}
        # ingest initial summary
        self.add(summary)

    def add(self, fec_summary: Dict[str, Any]) -> None:
        """
        Ingest a FEC summary payload dict, merging codeword stats under profile/timestamp.
        """
        cid = fec_summary.get('channel_id')
        if cid != self.channel_id:
            raise ValueError(f"Channel ID mismatch: expected {self.channel_id}, got {cid}")
        for profile in fec_summary.get('fec_summary_data', []):
            pid = profile.get('profile_id')
            if pid is None:
                continue
            for entry in profile.get('codeword_entries', []):
                ts = entry.get('timestamp')
                if ts is None:
                    continue
                self._data.setdefault(pid, {})
                self._data[pid].setdefault(ts, {})
                self._data[pid][ts].update(entry)

    def set_entry(self, profile_id: int, timestamp: int, data: Dict[str, Any]) -> None:
        """
        Replace or insert the entry dict for a specific profile and timestamp.

        Args:
            profile_id: The profile ID to target.
            timestamp:   The timestamp key.
            data:        Full entry dict to set (overwrites existing data).
        """
        self._data.setdefault(profile_id, {})
        # Overwrite the entire entry at that timestamp
        self._data[profile_id][timestamp] = data.copy()

    def set_field(self, profile_id: int, timestamp: int, key: str, value: Any) -> None:
        """
        Set or update a single field within an entry.

        Args:
            profile_id: The profile ID.
            timestamp:  The timestamp key.
            key:        Field name to set.
            value:      Field value to assign.
        """
        if profile_id not in self._data or timestamp not in self._data[profile_id]:
            raise KeyError(f"Entry not found for profile {profile_id} timestamp {timestamp}")
        self._data[profile_id][timestamp][key] = value

    def get_profile_ids(self) -> List[int]:
        """All profile IDs recorded."""
        return list(self._data.keys())

    def get_timestamps(self, profile_id: int) -> List[int]:
        """Sorted timestamps for a given profile."""
        return sorted(self._data.get(profile_id, {}).keys())

    def has_timestamp(self, profile_id: int, timestamp: int) -> bool:
        """Whether a timestamp exists for a profile."""
        return timestamp in self._data.get(profile_id, {})

    def get_entry(self, profile_id: int, timestamp: int) -> Dict[str, Any]:
        """Retrieve merged data dict for profile/timestamp."""
        return self._data[profile_id][timestamp]

    def to_dict(self) -> Dict[int, Dict[int, Dict[str, Any]]]:
        """Export nested data store."""
        return self._data