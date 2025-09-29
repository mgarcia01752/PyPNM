# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any, Dict, Iterator, List, Optional, Union, cast

from typing_extensions import deprecated
from pydantic import Field

from pypnm.api.routes.advance.common.types.types import (
    DeviceDetailsPayload, EntryDict, FlatIndex, GroupedIndex, Sort, SortOrder, TransactionFileCollection,)
from pypnm.api.routes.common.classes.file_capture.transaction_record_parser import DeviceDetailsModel
from pypnm.api.routes.common.classes.file_capture.types import TransactionRecord, TransactionRecordModel
from pypnm.docsis.data_type.sysDescr import SystemDescriptorModel, SystemDescriptor
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import ChannelId, MacAddressStr
from pypnm.pnm.process.pnm_parameter import PnmObjectAndParameters

class PnmCollectionModel(TransactionRecordModel):
    data: bytes  = Field(..., description="Raw file bytes (PNM stream).")

class PnmCollection:
    def __init__(self, trans_collection: TransactionFileCollection, trans_record: TransactionRecord) -> None:
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self.capture_group: TransactionFileCollection = trans_collection
        self.trans_record: TransactionRecord = trans_record  # keep reference (avoids unused param)

        self.index: FlatIndex = {}
        self.grouped: GroupedIndex = {}
        self._default_order: SortOrder = [Sort.CHANNEL_ID, Sort.ASCEND_EPOCH]

        self._process()

    def _process(self) -> None:
        self.index.clear()
        self.grouped.clear()

        for tx_id, filename, byte_stream in self.capture_group:
            
            self.logger.info("[_process] tx_id=%s file=%s data=%s", tx_id, filename, self._bytes_preview(byte_stream))

            try:
                params: Dict[str, Any] = PnmObjectAndParameters(byte_stream).to_dict()
                self.logger.debug("[_process] parsed params for %s -> %s", filename, params)
            except Exception as e:
                self.logger.error("Failed to parse parameters for %s: %s", filename, e)
                continue

            mac: Optional[str] = cast(Optional[str], params.get("mac_address"))
            if not mac:
                self.logger.error("Missing MAC for file '%s', skipping entry", filename)
                continue

            entry: EntryDict = {
                "transaction_id": tx_id,
                "file_name": cast(str, params.get("file_name") or filename),
                "file_type": cast(str, params.get("file_type") or "UNKNOWN"),
                "capture_time": cast(int, params.get("capture_time") or 0),
                "channel_id": cast(Optional[int], params.get("channel_id")),
                "device_details": cast(DeviceDetailsPayload, params.get("device_details")),
                "data": byte_stream,
                "mac_address": mac,
            }

            self.logger.debug(
                f"[_process] tx_id={tx_id}, entry mac={mac} ch={entry['channel_id']} "
                f"type={entry['file_type']} t={entry['capture_time']}"
            )

            mac_key = MacAddressStr(mac)
            self.index.setdefault(mac_key, []).append(entry)

            ch = entry["channel_id"]
            if ch is not None:
                ch_key = int(ch)
                self.grouped.setdefault(mac_key, {}).setdefault(ch_key, []).append(entry)

        self.logger.debug("[_process] complete mac_count=%d", len(self.index))

    def mac_addresses(self) -> List[MacAddressStr]:
        return list(self.index.keys())

    def grouped_by_mac_channel(self, sort: Optional[SortOrder] = None) -> GroupedIndex:
        if not sort:
            return self.grouped

        result: GroupedIndex = self.grouped

        if Sort.MAC_ADDRESS in sort:
            result = dict(OrderedDict(sorted(result.items(), key=lambda kv: kv[0])))

        if any(s in (Sort.ASCEND_EPOCH, Sort.PNM_FILE_TYPE) for s in sort):
            out: GroupedIndex = {}
            for mac, ch_map in result.items():
                new_ch_map: Dict[int, List[EntryDict]] = {}
                for ch_id, lst in ch_map.items():
                    seq = list(lst)
                    if Sort.ASCEND_EPOCH in sort:
                        seq.sort(key=lambda x: cast(int, x.get("capture_time", 0)))
                    if Sort.PNM_FILE_TYPE in sort:
                        seq.sort(key=lambda x: cast(str, x.get("file_type", "")))
                    new_ch_map[ch_id] = seq
                out[mac] = new_ch_map
            return out

        return result

    def iter_entries(
        self,
        mac: Optional[Union[MacAddressStr, MacAddress]] = None,
        channel_id: Optional[ChannelId] = None,
        sort: Optional[SortOrder] = None,
    ) -> Iterator[EntryDict]:
        if mac is not None and not isinstance(mac, str):
            mac = MacAddressStr(str(mac))

        grouped_view = self.grouped_by_mac_channel(sort=sort)

        mac_keys: List[MacAddressStr]
        if mac is not None:
            mac_keys = [mac] if mac in grouped_view else []
        else:
            mac_keys = list(grouped_view.keys())

        if sort and (Sort.MAC_ADDRESS in sort):
            mac_keys = sorted(mac_keys, key=lambda m: str(m))

        for m in mac_keys:
            ch_map = grouped_view.get(m, {})
            if channel_id is not None:
                ch_keys = [int(channel_id)] if int(channel_id) in ch_map else []
            else:
                ch_keys = list(ch_map.keys())

            if sort and (Sort.CHANNEL_ID in sort):
                ch_keys = sorted(ch_keys)

            for ch in ch_keys:
                seq = list(ch_map.get(ch, []))
                if sort and (Sort.ASCEND_EPOCH in sort):
                    seq.sort(key=lambda x: cast(int, x.get("capture_time", 0)))
                if sort and (Sort.PNM_FILE_TYPE in sort):
                    seq.sort(key=lambda x: cast(str, x.get("file_type", "")))
                for e in seq:
                    yield e

    def sort_inplace(self, order: Optional[SortOrder] = None) -> None:
        order = order or self._default_order

        if Sort.MAC_ADDRESS in order:
            self.grouped = dict(OrderedDict(sorted(self.grouped.items(), key=lambda kv: kv[0])))

        if Sort.CHANNEL_ID in order:
            self.grouped = {
                mac: dict(OrderedDict(sorted(ch_map.items(), key=lambda kv: kv[0])))
                for mac, ch_map in self.grouped.items()
            }

        if any(s in (Sort.ASCEND_EPOCH, Sort.PNM_FILE_TYPE) for s in order):
            for ch_map in self.grouped.values():
                for lst in ch_map.values():
                    if Sort.ASCEND_EPOCH in order:
                        lst.sort(key=lambda x: cast(int, x.get("capture_time", 0)))
                    if Sort.PNM_FILE_TYPE in order:
                        lst.sort(key=lambda x: cast(str, x.get("file_type", "")))

    def to_model(self, mac_address: MacAddress = MacAddress(MacAddress.null())) -> List[PnmCollectionModel]:
        records: List[PnmCollectionModel] = []
        txn = 0

        if not mac_address.null():
            mac_str = str(mac_address)
            selected = {MacAddressStr(mac_str): self.index.get(MacAddressStr(mac_str), [])}
            self.logger.debug("[to_model] filter mac=%s count=%d", mac_str, len(selected[MacAddressStr(mac_str)]))
            if not selected[MacAddressStr(mac_str)]:
                self.logger.warning("No entries found for MAC address: %s", mac_str)
        else:
            selected = self.index
            self.logger.debug("[to_model] filter mac=ALL mac_count=%d", len(selected))

        for mac_key, mac_entries in selected.items():
            self.logger.info("Building model records for MAC: %s", mac_key)

            for e in mac_entries:
                txn += 1

                filename        = cast(str, e.get("file_name") or "")
                file_type       = cast(str, e.get("file_type") or "UNKNOWN")
                capture_time    = cast(int, e.get("capture_time") or 0)
                device_raw      = cast(DeviceDetailsPayload, e.get("device_details"))
                data            = cast(bytes, e.get("data") or b"")

                self.logger.debug(
                    f"[to_model] txn={txn} mac={mac_key} file={filename} "
                    f"type={file_type} t={capture_time} data={self._bytes_preview(data)}"
                )

                sys_model = self._coerce_system_description(device_raw)
                dev_details = DeviceDetailsModel(system_description=sys_model)

                model = PnmCollectionModel(
                    transaction     =   txn,
                    capture_time    =   capture_time,
                    mac_address     =   mac_key,
                    file_type       =   self._derive_pnm_test_type(file_type),
                    filename        =   filename,
                    device_details  =   dev_details,
                    data            =   data,
                )
                records.append(model)

        records.sort(key=lambda m: (m.capture_time, m.mac_address, m.transaction))
        self.logger.debug("[to_model] complete records=%d", len(records))
        return records

    @deprecated("Use to_model() instead")
    def get_DEPRECATE(self, sort: Optional[List[Sort]] = None) -> Dict[str, Dict[int, List[Dict[str, Any]]]]:
        return {}

    @staticmethod
    def _derive_pnm_test_type(file_type_code: str) -> str:
        return file_type_code

    @staticmethod
    def _coerce_system_description(payload: DeviceDetailsPayload) -> SystemDescriptorModel:
        try:
            if isinstance(payload, SystemDescriptorModel):
                return payload
            if isinstance(payload, dict):
                if "system_description" in payload:
                    return PnmCollection._coerce_system_description(cast(DeviceDetailsPayload, payload["system_description"]))
                sys_keys = {"HW_REV", "VENDOR", "BOOTR", "SW_REV", "MODEL"}
                if any(k in payload for k in sys_keys):
                    return SystemDescriptor.load_from_dict(payload).to_model()
            if isinstance(payload, SystemDescriptor):
                return payload.to_model()
            if isinstance(payload, str):
                return SystemDescriptor.parse(payload).to_model()
        except Exception:
            pass
        return SystemDescriptor.empty().to_model()

    @staticmethod
    def _bytes_preview(b: bytes, n: int = 16) -> str:
        if not b:
            return "bytes(0)"
        head = b[:n].hex()
        return f"bytes(len={len(b)}, head=0x{head}...)"

    @staticmethod
    def _type_name(x: Any) -> str:
        return type(x).__name__
