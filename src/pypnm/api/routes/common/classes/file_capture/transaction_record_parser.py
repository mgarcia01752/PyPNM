# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from typing import Optional, Dict, Any

from pypnm.api.routes.advance.common.types.types import TransactionId

from pypnm.api.routes.common.classes.file_capture.types import DeviceDetailsModel, TransactionRecordModel
from pypnm.docsis.cable_modem import MacAddress
from pypnm.docsis.data_type.sysDescr import SystemDescriptor
from pypnm.lib.types import FileName, MacAddressStr, TimestampSec

class TransactionRecordParser:
    """
    Wrapper class for a single PNM file transaction record.
    Provides easy access to core attributes like MAC, timestamp, test type, etc.
    """

    def __init__(self, transaction_id: TransactionId):
        self.transaction_id:TransactionId = transaction_id

        # TODO: Refactor to use PnmFileTransaction internally, this is causing circular imports
        from pypnm.api.routes.common.classes.file_capture.pnm_file_transaction import PnmFileTransaction
        self.record: Optional[Dict[str, Any]] = PnmFileTransaction().get_record(transaction_id)

        if not self.record:
            raise ValueError(f"No record found for transaction ID: {transaction_id}")

    def get_timestamp(self) -> TimestampSec:
        return self.record.get("timestamp")

    def get_mac_address(self) -> MacAddressStr:
        return self.record.get("mac_address")

    def get_test_type(self) -> str:
        return self.record.get("pnm_test_type")

    def get_filename(self) -> FileName:
        return self.record.get("filename")
    
    def get_device_details(self) -> Optional[Dict[str, Any]]:
        return self.record.get("device_details", {}).get("system_description", {}) if self.record else None

    def get_device_model(self) -> Optional[str]:
        device_details = self.get_device_details()
        return device_details.get("MODEL") if device_details else None

    '''
        System Descriptor
    '''

    def get_device_vendor(self) -> Optional[str]:
        device_details = self.get_device_details()
        return device_details.get("VENDOR") if device_details else None

    def get_software_revision(self) -> Optional[str]:
        device_details = self.get_device_details()
        return device_details.get("SW_REV") if device_details else None

    def get_hardware_revision(self) -> Optional[str]:
        device_details = self.get_device_details()
        return device_details.get("HW_REV") if device_details else None

    def get_bootrom_version(self) -> Optional[str]:
        device_details = self.get_device_details()
        return device_details.get("BOOTR") if device_details else None

    # ─────────────────────────────────────────────────────────────
    # New: Pydantic models and conversion helpers
    # ─────────────────────────────────────────────────────────────

    def to_model(self) -> TransactionRecordModel:
        """
        Build a Pydantic model for this transaction, normalizing device_details via:
            SystemDescriptor.load_from_dict(...).to_model()
        """
        sys_dict = self.get_device_details() or {}
        sdm = SystemDescriptor.load_from_dict(sys_dict).to_model()

        return TransactionRecordModel(
            transaction_id  =   self.transaction_id,
            timestamp       =   self.get_timestamp(),
            mac_address     =   self.get_mac_address() or MacAddressStr(MacAddress.null()),
            pnm_test_type   =   self.get_test_type() or "",
            filename        =   self.get_filename(),
            device_details  =   DeviceDetailsModel(system_description=sdm),
        )

    @classmethod
    def from_id(cls, transaction_id: TransactionId) -> TransactionRecordModel:
        """
        Convenience constructor that returns the validated model directly.
        """
        return cls(transaction_id).to_model()
