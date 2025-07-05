# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Optional, Dict, Any
from pypnm.api.routes.common.classes.file_capture.pnm_file_transaction import PnmFileTransaction


class TransactionRecordParser:
    """
    Wrapper class for a single PNM file transaction record.
    Provides easy access to core attributes like MAC, timestamp, test type, etc.
    """

    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        self.record: Optional[Dict[str, Any]] = PnmFileTransaction().get_record(transaction_id)

        if not self.record:
            raise ValueError(f"No record found for transaction ID: {transaction_id}")

    def get_timestamp(self) -> Optional[int]:
        return self.record.get("timestamp")

    def get_mac_address(self) -> Optional[str]:
        return self.record.get("mac_address")

    def get_test_type(self) -> Optional[str]:
        return self.record.get("pnm_test_type")

    def get_filename(self) -> Optional[str]:
        return self.record.get("filename")

    def get_device_details(self) -> Optional[Dict[str, Any]]:
        return self.record.get("device_details", {}).get("sys_descr", {})

    def get_device_model(self) -> Optional[str]:
        return self.get_device_details().get("MODEL")

    def get_device_vendor(self) -> Optional[str]:
        return self.get_device_details().get("VENDOR")

    def get_software_revision(self) -> Optional[str]:
        return self.get_device_details().get("SW_REV")

    def get_hardware_revision(self) -> Optional[str]:
        return self.get_device_details().get("HW_REV")

    def get_bootrom_version(self) -> Optional[str]:
        return self.get_device_details().get("BOOTR")
