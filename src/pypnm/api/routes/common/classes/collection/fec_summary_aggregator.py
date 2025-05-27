# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Any, Dict, List, Optional

from pypnm.pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary


class FecSummaryAggregator:
    """
    Aggregates FEC summary data by channel directly in a master dictionary.

    Adds accept CmDsOfdmFecSummary service instances and merges their data
    into a nested dict: channel_id -> profile_id -> timestamp -> entry.

    After the first add, all subsequent summaries must share the same MAC address.
    """
    def __init__(self):
        """
        Initialize an empty master data store and unset MAC.
        """
        self._data: Dict[int, Dict[int, Dict[int, Dict[str, Any]]]] = {}
        self._mac_address: Optional[str] = None

    def add(self, summary_service: CmDsOfdmFecSummary) -> None:
        """
        Ingest a FEC summary service instance, merging its data.

        Raises:
            ValueError: if channel_id or mac_address is missing,
                        or if MAC mismatches a previous summary.
        """
        summary = summary_service.to_dict()
        cid = summary.get('channel_id')
        mac = summary.get('mac_address')
        if cid is None:
            raise ValueError("Missing channel_id in FEC summary")
        if mac is None:
            raise ValueError("Missing mac_address in FEC summary")
        # Enforce same MAC address after first add
        if self._mac_address is None:
            self._mac_address = mac
        elif mac != self._mac_address:
            raise ValueError(
                f"MAC address mismatch: expected {self._mac_address}, got {mac}"
            )
        # Merge entries
        for profile in summary.get('fec_summary_data', []):
            pid = profile.get('profile_id')
            if pid is None:
                continue
            for entry in profile.get('codeword_entries', []):
                ts = entry.get('timestamp')
                if ts is None:
                    continue
                # insert/overwrite entry
                self._data.setdefault(cid, {}).setdefault(pid, {})[ts] = entry.copy()

    def get_channel_ids(self) -> List[int]:
        """
        Retrieve a sorted list of all channel IDs for which RxMER captures have been ingested.

        Returns:
            List[int]: Channel IDs currently stored in this aggregator, in ascending order.
        """
        return sorted(self._data.keys())

    def get_profile_ids(self, channel_id: int) -> List[int]:
        """Return sorted list of profile IDs for a channel."""
        return sorted(self._data.get(channel_id, {}).keys())

    def get_timestamps(self, channel_id: int, profile_id: int) -> List[int]:
        """Return sorted list of timestamps for a given channel and profile."""
        return sorted(self._data.get(channel_id, {}).get(profile_id, {}).keys())

    def has_entry(self, channel_id: int, profile_id: int, timestamp: int) -> bool:
        """Check existence of data for channel/profile/timestamp."""
        return (
            channel_id in self._data and
            profile_id in self._data[channel_id] and
            timestamp in self._data[channel_id][profile_id]
        )

    def get_entry(self, channel_id: int, profile_id: int, timestamp: int) -> Dict[str, Any]:
        """Retrieve entry for channel/profile/timestamp; raises KeyError if missing."""
        return self._data[channel_id][profile_id][timestamp]

    def to_dict(self) -> Dict[int, Dict[int, Dict[int, Dict[str, Any]]]]:
        """Export the entire master data store."""
        return self._data
    
    def get_summary_totals(
        self,
        channel_id: int,
        start_time: int,
        end_time: int
    ) -> Dict[int, Dict[str, int]]:
        """
        Aggregate FEC summary counters per profile between two timestamps (inclusive).

        Args:
            channel_id: ID of the channel to summarize.
            start_time: Lower bound timestamp (inclusive).
            end_time: Upper bound timestamp (inclusive).

        Returns:
            A dict mapping profile_id to a dict of summed counters.
        Raises:
            KeyError: if no data exists for the given channel.
        """
        if channel_id not in self._data:
            raise KeyError(f"No data for channel {channel_id}")

        summary: Dict[int, Dict[str, int]] = {}
        for profile_id, ts_entries in self._data[channel_id].items():
            agg: Dict[str, int] = {}
            
            for ts, entry in ts_entries.items():
                if ts < start_time or ts > end_time:
                    continue
            
                for key, val in entry.items():
                    # Skip the timestamp field and non-numeric values
                    if key == "timestamp" or not isinstance(val, (int, float)):
                        continue
                    agg[key] = agg.get(key, 0) + int(val)
            
            summary[profile_id] = agg

        return summary
