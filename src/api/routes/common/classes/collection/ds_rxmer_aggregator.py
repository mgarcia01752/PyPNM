# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Dict, List, Any, Optional
from api.routes.common.classes.analysis.analysis import Analysis
from pnm.lib.min_avg_max import MinAvgMax
from pnm.process.CmDsOfdmRxMer import CmDsOfdmRxMer

class DsRxMerAggregator:
    """
    Aggregates RxMER captures by channel and timestamp.

    - Ingests `CmDsOfdmRxMer` service instances via `add()`.
    - Enforces a single MAC address for all ingested summaries.
    - Stores captures per `channel_id` in ascending `capture_time` order.
    - Provides total count, per-channel timestamps, raw service retrieval, and Min/Avg/Max stats.
    """
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._mac_address: Optional[str] = None
        self._store: Dict[int, List[Dict[str, Any]]] = {}

    def add(self, rxmer_service: CmDsOfdmRxMer) -> None:
        """
        Ingest a CmDsOfdmRxMer instance.

        Args:
            rxmer_service: The service object to ingest. Must implement `to_dict()`.

        Raises:
            ValueError: On missing fields or MAC mismatch.
        """
        summary:Dict[str, object] = rxmer_service.to_dict()
        mac = summary.get('mac_address')
        if mac is None:
            raise ValueError("RxMER summary missing 'mac_address'")
        # Enforce consistent MAC
        if self._mac_address is None:
            self._mac_address = mac
        elif mac != self._mac_address:
            raise ValueError(
                f"MAC address mismatch: expected {self._mac_address}, got {mac}"
            )

        channel_id:int = summary.get('channel_id',) # type: ignore
        if channel_id is None:
            raise ValueError("RxMER summary missing 'channel_id'")

        capture_time:int = summary.get('pnm_header', {}).get('capture_time') # type: ignore

        if capture_time is None:
            raise ValueError("RxMER summary missing 'capture_time'")

        # Append and sort by capture_time
        bucket = self._store.setdefault(channel_id, [])
        bucket.append({'capture_time': capture_time, 'service': rxmer_service})
        bucket.sort(key=lambda x: x['capture_time'])

    def get_channel_ids(self) -> List[int]:
        """
        Retrieve a sorted list of all channel IDs for which RxMER captures have been ingested.

        Returns:
            List[int]: Channel IDs currently stored in this aggregator, in ascending order.
        """
        return sorted(self._store.keys())
    
    def length(self) -> int:
        """
        Total number of RxMER captures ingested across all channels.
        """
        return sum(len(lst) for lst in self._store.values())

    def get_capture_times(self, channel_id: int) -> List[Any]:
        """
        List all capture_time values for a channel, sorted ascending.

        Args:
            channel_id: The channel ID to query.

        Returns:
            List of capture_time values. Empty list if channel not present.
        """
        return [item['capture_time'] for item in self._store.get(channel_id, [])]

    def get(self, channel_id: int, capture_time: Any) -> CmDsOfdmRxMer:
        """
        Retrieve the original `CmDsOfdmRxMer` instance for a specific channel and capture_time.

        Args:
            channel_id: The channel ID to query.
            capture_time: The capture_time to retrieve.

        Returns:
            The `CmDsOfdmRxMer` service object associated with that timestamp.

        Raises:
            KeyError: If the channel or timestamp is not found.
        """
        bucket = self._store.get(channel_id)
        if bucket is None:
            raise KeyError(f"No captures for channel {channel_id}")
        for entry in bucket:
            if entry['capture_time'] == capture_time:
                return entry['service']
        raise KeyError(f"Capture time {capture_time} not found for channel {channel_id}")

    def getMinAvgMin(self, channel_id: int) -> MinAvgMax:
        """
        Compute Min/Avg/Max of the RxMER values for a given channel.

        Args:
            channel_id: The channel ID to compute stats for.

        Returns:
            A MinAvgMax instance initialized with the channel's RxMER values.

        Raises:
            KeyError: If no captures exist for the channel.
        """
        bucket = self._store.get(channel_id)
        if not bucket:
            raise KeyError(f"No RxMER captures for channel {channel_id}")

        values: List[List[float]] = []

        for entry in bucket:
            service: CmDsOfdmRxMer = entry['service']
            summary: Dict[str, Any] = service.to_dict()

            mer_values = summary.get("values")
            if not isinstance(mer_values, list):
                raise ValueError(f"'values' must be a list of numbers, got {type(mer_values)}")

            values.append(mer_values)

        return MinAvgMax(values)

    def getBasicAnalysis(self, channel_id: Optional[int] = None, capture_time: Optional[Any] = None) -> Any:
        """
        Perform basic RxMER analysis via Analysis.basic_analysis_rxmer.

        - If channel_id is None: return a dict mapping each channel_id to its analysis result.
        - If channel_id is provided and capture_time is None: return analysis for all captures in that channel.
        - If both channel_id and capture_time are provided: return analysis for that single capture.

        Raises:
            ValueError: if capture_time is provided without channel_id.
            KeyError: if the specified channel or capture_time does not exist.
        """
        # Invalid combination
        if capture_time is not None and channel_id is None:
            raise ValueError("capture_time cannot be provided without channel_id")

        # Aggregate across all channels
        if channel_id is None:
            results: Dict[int, Any] = {}
            for chan_id in self._store.keys():
                # build list of per-capture dicts
                data = [entry['service'].to_dict() for entry in self._store[chan_id]]
                results[chan_id] = Analysis.basic_analysis_rxmer(data)
            return results

        # Specific channel
        bucket = self._store.get(channel_id)
        if bucket is None:
            raise KeyError(f"No captures for channel {channel_id}")

        # Single capture
        if capture_time is not None:
            svc = self.get(channel_id, capture_time)
            return Analysis.basic_analysis_rxmer(svc.to_dict())

        # Entire channel
        data = [entry['service'].to_dict() for entry in bucket]
        return Analysis.basic_analysis_rxmer(data)
