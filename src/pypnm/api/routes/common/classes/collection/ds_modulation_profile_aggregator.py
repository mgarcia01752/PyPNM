# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from api.routes.common.classes.analysis.analysis import Analysis
from pypnm.pnm.process.CmDsOfdmModulationProfile import CmDsOfdmModulationProfile

class DsModulationProfileAggregator:
    """
    Aggregates OFDM modulation profiles by channel and timestamp.

    - Ingests `CmDsOfdmModulationProfile` service instances via `add()`.
    - Enforces a single MAC address for all ingested profiles.
    - Stores profiles per `channel_id` in ascending `capture_time` order.
    - Provides total count, per-channel capture times, raw service retrieval, profile extraction,
      and basic analysis via Analysis.basic_analysis_ds_modulation_profile.
    """
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._mac_address: Optional[str] = None
        self._store: Dict[int, List[Dict[str, Any]]] = {}

    def add(self, modprof_service: CmDsOfdmModulationProfile) -> None:
        """
        Ingest a CmDsOfdmModulationProfile instance.

        Args:
            modprof_service: The service object to ingest. Must implement `to_dict()`.

        Raises:
            ValueError: On missing fields or MAC mismatch.
        """
        summary = modprof_service.to_dict()
        mac = summary.get('mac_address')
        if mac is None:
            raise ValueError("ModProfile summary missing 'mac_address'")
        # Enforce consistent MAC
        if self._mac_address is None:
            self._mac_address = mac
        elif mac != self._mac_address:
            raise ValueError(
                f"MAC address mismatch: expected {self._mac_address}, got {mac}"
            )

        channel_id = summary.get('channel_id')
        if channel_id is None:
            raise ValueError("ModProfile summary missing 'channel_id'")

        capture_time = summary.get('pnm_header', {}).get('capture_time')
        if capture_time is None:
            raise ValueError("ModProfile summary missing 'capture_time'")

        # Append and sort by capture_time
        bucket = self._store.setdefault(channel_id, [])
        bucket.append({'capture_time': capture_time, 'service': modprof_service})
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
        Total number of modulation profiles ingested across all channels.
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

    def get(
        self,
        channel_id: int,
        capture_time: Any,
        *,
        find_closest: bool = False
    ) -> Tuple[bool, Optional[CmDsOfdmModulationProfile]]:
        """
        Retrieve the CmDsOfdmModulationProfile for a channel/timestamp.

        Args:
            channel_id: ID of the channel to query.
            capture_time: Desired capture_time.
            find_closest: If True and no exact match is found, return the profile
                        whose timestamp is nearest to `capture_time`.

        Returns:
            (found, profile_or_None). `found` is True if we returned an exact or
            (if allowed) closest match; otherwise False.
        """
        bucket = self._store.get(channel_id) or []
        self.logger.debug(f"Looking in channel {channel_id}, bucket: {bucket!r}")

        # 1) Try exact match
        for entry in bucket:
            ts = entry.get("capture_time")
            if ts == capture_time:
                return True, entry.get("service")

        # 2) Optionally try closest match
        if find_closest and bucket:
            # Filter out entries without a comparable timestamp
            valid = [(entry, entry["capture_time"]) 
                    for entry in bucket 
                    if isinstance(entry.get("capture_time"), (int, float))]
            if valid:
                # Pick the entry with minimal |ts - capture_time|
                closest_entry, closest_ts = min(
                    valid,
                    key=lambda pair: abs(pair[1] - capture_time)
                )
                self.logger.debug(
                    f"No exact match; using closest ts={closest_ts}"
                )
                return True, closest_entry.get("service")

        # 3) Nothing found
        return False, None


    def get_profiles(self, channel_id: int, capture_time: Any) -> List[Dict[str, Any]]:
        """
        Extract the pre-process list of modulation profiles for a specific capture.

        Args:
            channel_id: The channel ID.
            capture_time: The capture_time to retrieve.

        Returns:
            List of profile dicts, each containing 'profile_id', 'carriers', etc.

            "profiles": [                
                'profile_id': , 
                'schemes': [
                    {
                        'schema_type': , 
                        'modulation_order':, 
                        'num_subcarriers':
                    }
                ]
            }        

        Raises:
            KeyError: If the channel or timestamp is not found.
        """
        service = self.get(channel_id, capture_time)
        summary = service.to_dict()
        return summary.get('profiles', [])

    def get_profile_ids(self, channel_id: int, capture_time: Any) -> List[int]:
        """
        List all profile IDs for a specific channel snapshot.

        Args:
            channel_id: The channel ID.
            capture_time: The capture_time to query.

        Returns:
            Sorted list of profile IDs.
        """
        profiles = self.get_profiles(channel_id, capture_time)
        return sorted(p.get('profile_id') for p in profiles if 'profile_id' in p)

    def basic_analysis(self, channel_id: Optional[int] = None, 
                       capture_time: Optional[Any] = None) -> Union[Dict[int, Any], Any]:
        """
        Perform basic modulation profile analysis via Analysis.basic_analysis_ds_modulation_profile.

        - If channel_id is None: returns a dict mapping channel_id to its analysis result.
        - If channel_id is provided and capture_time is None: analyzes all captures for that channel.
        - If both channel_id and capture_time are provided: analyzes a single capture.

        Raises:
            ValueError: if capture_time is provided without channel_id.
            KeyError: if the specified channel or capture_time does not exist.

        Return:            
        {
            "pnm_header": {
                "file_type": "PNN",
                "file_type_version": 10,
                "major_version": 1,
                "minor_version": 0,
                "capture_time": 618052
            },
            "channel_id": 33,
            "frequency_unit": "Hz",
            "shannon_limit_unit": "dB",
            "profiles": [
                {
                    "profile_id": 3,
                    "carrier_values": {
                            "frequency":{...},
                            "modulation": {...},
                            "shannon_limit": {...}
                }
            ]
        }
        """
        results: Dict[int, Any] = {}
        self.logger.debug(f'[basic_analysis] - ChannelID: {channel_id} - CaptureTime: {capture_time}')
         
        # Invalid combination
        if capture_time is not None and channel_id is None:
            raise ValueError("capture_time cannot be provided without channel_id")

        # Analysis across all channels
        if channel_id is None:
            self.logger.debug(f'[basic_analysis] - Processing all Channel ID(s)')
            for cid, bucket in self._store.items():
                data = [entry['service'].to_dict() for entry in bucket]
                results[cid] = Analysis.basic_analysis_ds_modulation_profile(data)
            return results

        # Specific channel
        bucket = self._store.get(channel_id)
        if bucket is None:
            raise KeyError(f"[basic_analysis] - No profiles for channel {channel_id}")

        # Single capture
        if capture_time is not None:
            self.logger.debug(f'[basic_analysis] - Single Capture: ChannelID: {channel_id} - Capture: {capture_time}')
            
            service:CmDsOfdmModulationProfile
            status, service = self.get(channel_id, capture_time, find_closest=True)
            if not status:
                raise KeyError(f"[basic_analysis] - CmDsOfdmModulationProfile Not Found or was not captured")
            
            self.logger.debug(f'[basic_analysis] - Single Capture: {service}')
            badmp = Analysis.basic_analysis_ds_modulation_profile(service.to_dict())
            return badmp

        # Entire channel
        self.logger.debug(f'[basic_analysis] - Processing all Captures')
        data = [entry['service'].to_dict() for entry in bucket][0]
        return Analysis.basic_analysis_ds_modulation_profile(data)

    def to_dict(self) -> Dict[int, Dict[Any, List[Dict[str, Any]]]]:
        """
        Export the entire aggregation as a nested dict:
            { channel_id: { capture_time: profiles_list } }
        """
        result: Dict[int, Dict[Any, List[Dict[str, Any]]]] = {}
        for cid, bucket in self._store.items():
            result[cid] = {entry['capture_time']: entry['service'].to_dict().get('profiles', [])
                           for entry in bucket}
        return result
