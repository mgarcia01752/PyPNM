# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import enum
import logging
from typing import Any, Dict, List, Tuple
from collections import OrderedDict

from pnm.process.pnm_parameter import PnmObjectAndParameters


class Sort(enum.Enum):
    """
    Sorting strategies for PnmCollection.get().

    - CHANNEL_ID: group entries by channel (implicit grouping).
    - ASCEND_EPOCH: sort captures by `capture_time` ascending within each channel.
    - PNM_FILE_TYPE: sort captures by `file_type` within each channel.
    - MAC_ADDRESS: sort top-level MAC keys lexically.
    """
    CHANNEL_ID = enum.auto()
    ASCEND_EPOCH = enum.auto()
    PNM_FILE_TYPE = enum.auto()
    MAC_ADDRESS = enum.auto()


class PnmCollection:
    """
    Manage and query a set of PNM capture files.

    - Build an index by MAC address
    - Group captures by channel ID
    - Support multi-stage sorting of the results

    Usage:
        coll = PnmCollection(capture_group)
        # Default: group by channel, then sort by timestamp
        results = coll.get()
    """

    def __init__(
        self,
        capture_group: List[Tuple[str, bytes]]
    ) -> None:
        """
        Initialize and index the capture group.

        Args:
            capture_group: List of (filename, raw_bytes) tuples.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.capture_group = capture_group
        self.index: Dict[str, List[Dict[str, Any]]] = {}
        self._process()

    def _process(self) -> None:
        """
        Populate `self.index` mapping MAC -> list of entry dicts:
          - file_name: original filename
          - file_type: 4-char PNM code
          - capture_time: epoch seconds
          - channel_id: channel identifier
          - data: raw byte stream
        """
        self.index.clear()

        for filename, byte_stream in self.capture_group:
            params = PnmObjectAndParameters(byte_stream).to_dict()
            entry = {
                "file_name": filename,
                "file_type": params.get("file_type"),
                "capture_time": params.get("capture_time"),
                "channel_id": params.get("channel_id"),
                "data": byte_stream
            }
            mac = params.get("mac_address")
            if not mac:
                self.logger.error(f"Missing MAC for file '{filename}', skipping entry")
                continue
            self.index.setdefault(mac, []).append(entry)

    def get(
        self,
        sort: List[Sort] = [Sort.CHANNEL_ID, Sort.ASCEND_EPOCH]
    ) -> Dict[Any, Any]:
        """
        Retrieve captures grouped by MAC and channel, applying sorts in sequence.

        Args:
            sort: Ordered list of Sort enums. Default: [CHANNEL_ID, ASCEND_EPOCH].

        Returns:
            Nested dict of form:
                {
                  mac_address: {
                      channel_id: [entry_dict, ...],
                      ...
                  },
                  ...
                }
            Sort stages:
              - CHANNEL_ID: implicit grouping by channel.
              - ASCEND_EPOCH: sort each channel list by capture_time.
              - PNM_FILE_TYPE: then sort by file_type.
              - MAC_ADDRESS: reorder top-level keys lexically.
        """
        # 1) Build nested grouping: MAC -> channel_id -> list of entries
        nested: Dict[str, Dict[int, List[Dict[str, Any]]]] = {}
        for mac, entries in self.index.items():
            channel_map: Dict[int, List[Dict[str, Any]]] = {}
            for e in entries:
                ch = e.get("channel_id")
                if ch is None:
                    continue
                channel_map.setdefault(ch, []).append(e.copy())
            nested[mac] = channel_map

        # 2) Apply each sort stage
        result = nested
        for strategy in sort:
            if strategy == Sort.CHANNEL_ID:
                # grouping is already in place
                continue

            if strategy == Sort.ASCEND_EPOCH:
                for ch_map in result.values():
                    for lst in ch_map.values():
                        lst.sort(key=lambda x: x.get("capture_time", 0))
            elif strategy == Sort.PNM_FILE_TYPE:
                for ch_map in result.values():
                    for lst in ch_map.values():
                        lst.sort(key=lambda x: x.get("file_type", ""))
            elif strategy == Sort.MAC_ADDRESS:
                ordered = OrderedDict(sorted(result.items(), key=lambda kv: kv[0]))
                result = dict(ordered)
            else:
                self.logger.warning(f"Unknown sort strategy: {strategy}")
        
        return result
