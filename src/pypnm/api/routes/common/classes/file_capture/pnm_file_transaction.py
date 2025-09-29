from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
import hashlib
import time
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime

from pypnm.api.routes.common.classes.file_capture.transaction_record_parser import TransactionRecordParser
from pypnm.api.routes.common.classes.file_capture.types import TransactionRecordModel
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type.sysDescr import SystemDescriptor
from pypnm.lib.mac_address import MacAddress
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest


class PnmFileTransaction:
    """
    Manages persistent tracking of PNM file transactions across the PyPNM system.

    Each transaction corresponds to a PNM test result file (e.g., RxMER, Spectrum Analysis),
    whether generated through automated measurements or manually uploaded by a user.

    A transaction includes:
        - A unique transaction ID (16-char SHA-256 digest)
        - Timestamp (epoch time)
        - MAC address of the cable modem
        - PNM test type (e.g., DS_RXMER, SPECTRUM_ANALYZER)
        - Filename of the associated binary data file

    Transactions are stored in a central JSON file defined in system config at:
    `PnmFileRetrieval.transaction_db`.

    Usage Scenarios:
        - When a measurement test completes and produces a file.
        - When a user uploads a file manually via the REST API.
        - When retrieving metadata about previously captured test files.

    Attributes:
        transaction_db_path (Path): Path to the JSON file where all transactions are recorded.

    Record:
        {
            "<transaction_id>": {
                "timestamp": int,
                "mac_address": "<cable modem mac address>",
                "pnm_test_type": "<PNM Test Type>",
                "filename": "<FileName>",
                "device_details": {
                    "system_description": { ... }
                }
            }
        }
    """

    PNM_TEST_TYPE = "pnm_test_type"
    FILE_NAME = "filename"
    DEVICE_DETAILS = "device_details"

    def __init__(self):
        self.transaction_db_path = Path(SystemConfigSettings.transaction_db)
        self.transaction_db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.transaction_db_path.exists():
            self.transaction_db_path.write_text(json.dumps({}))

    async def insert(self, cable_modem: CableModem, pnm_test_type: DocsPnmCmCtlTest, filename: str) -> str:
        """
        Records a transaction initiated from an actual cable modem test.
        """
        sd: SystemDescriptor = await cable_modem.getSysDescr()
        return self._insert_generic(
            mac_address     = cable_modem.get_mac_address(),
            pnm_test_type   = pnm_test_type,
            filename        = filename,
            system_description=sd.to_dict(),
        )

    @staticmethod
    def set_file_by_user(mac_address: MacAddress, pnm_test_type: DocsPnmCmCtlTest, filename: str) -> str:
        """
        Records a transaction manually initiated by a user (e.g., uploaded file).
        """
        txn = PnmFileTransaction()
        return txn._insert_generic(
            mac_address=mac_address,
            pnm_test_type=pnm_test_type,
            filename=filename,
        )

    # ---------------------------
    # Safe read helpers (no recursion)
    # ---------------------------

    def _load_record_dict(self, transaction_id: str) -> dict | None:
        """
        Load the raw JSON record for a transaction_id directly from disk.
        """
        db = self._load_db()
        return db.get(transaction_id)

    def get_record(self, transaction_id: str) -> dict | None:
        """
        Return a plain dictionary representation of a transaction record, or None.
        """
        rec = self._load_record_dict(transaction_id)
        return rec if rec else None

    # Optional convenience alias if other code expects .get(...)
    def get(self, transaction_id: str) -> dict | None:
        return self.get_record(transaction_id)

    def getRecordModel(self, transaction_id: str) -> TransactionRecordModel:
        """
        Return a Pydantic model for a transaction record, or a null() model if missing.
        """
        rec = self._load_record_dict(transaction_id)
        if not rec:
            return TransactionRecordModel.null()
        # Delegate to the parser to construct the canonical model
        return TransactionRecordParser.from_id(transaction_id)

    def get_file_info_via_macaddress(self, mac_address: MacAddress) -> Optional[list[dict]]:
        """
        Find all transactions for a given MAC address.
        """
        db = self._load_db()
        mac_str = str(mac_address).lower()
        results: list[dict] = []

        for txn_id, record in db.items():
            if record.get("mac_address", "").lower() == mac_str:
                results.append(
                    {
                        "transaction_id": txn_id,
                        "pnm_test_type": record.get("pnm_test_type"),
                        "filename": record.get("filename"),
                        "timestamp": datetime.utcfromtimestamp(record.get("timestamp", 0)).strftime(
                            "%Y-%m-%d %H:%M:%S UTC"
                        ),
                        "device_details": record.get("device_details", {}),
                    }
                )

        return results if results else None

    # ---------------------------
    # Write helpers
    # ---------------------------

    def _insert_generic(
        self,
        mac_address: MacAddress,
        pnm_test_type: DocsPnmCmCtlTest,
        filename: str,
        system_description: Dict[str, str] | None = None,
    ) -> str:
        """
        Common logic for creating a transaction record.
        """
        timestamp = int(time.time())
        hash_input = f"{filename}{timestamp}".encode("utf-8")
        transaction_id = hashlib.sha256(hash_input).hexdigest()[:16]

        db = self._load_db()
        db[transaction_id] = {
            "timestamp": timestamp,
            "mac_address": str(mac_address),
            "pnm_test_type": pnm_test_type.name,
            "filename": filename,
            "device_details": {
                "system_description": system_description or {},
            },
        }
        self._save_db(db)
        return transaction_id

    def _load_db(self) -> dict:
        """
        Load the transaction database from JSON; return {} on parse errors.
        """
        try:
            with self.transaction_db_path.open("r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_db(self, db: dict) -> None:
        """
        Persist the transaction database to disk.
        """
        with self.transaction_db_path.open("w") as f:
            json.dump(db, f, indent=4)
