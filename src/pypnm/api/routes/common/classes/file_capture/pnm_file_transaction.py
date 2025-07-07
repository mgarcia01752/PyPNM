# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from datetime import datetime
import json
import hashlib
import time
from typing import Dict, Optional
from pathlib import Path

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

    Methods:
        set(cable_modem, pnm_test_type, filename): Creates and stores a new transaction.
        set_file_by_user(mac_address, pnm_test_type, filename): Creates a transaction without a full CableModem object.
        get(transaction_id): Retrieves metadata for a given transaction ID.
        _load_db(): Reads and parses the transaction database file.
        _save_db(data): Writes updated transaction data back to disk.
        
    Record:
    
        {
            "<transaction_id>": {
                "timestamp":int <EPHOC>,
                "mac_address":MacAddress "<cable modem mac address>",
                "pnm_test_type":str "<PNM Test Type>",
                "filename":str "<FileName>",
                "device_details": {
                    "sys_descr":Dict[str,str] ,
                }
            }
        }    
    
    """

    PNM_TEST_TYPE = 'pnm_test_type'
    FILE_NAME = 'filename'

    def __init__(self):
        """Initializes the transaction manager and prepares the transaction database path."""
        self.transaction_db_path = Path(SystemConfigSettings.transaction_db)
        self.transaction_db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.transaction_db_path.exists():
            self.transaction_db_path.write_text(json.dumps({}))

    async def insert(self, cable_modem: CableModem, pnm_test_type: DocsPnmCmCtlTest, filename: str) -> str:
        """
        Records a transaction initiated from an actual cable modem test.

        Args:
            cable_modem (CableModem): Cable modem instance used to retrieve the MAC address.
            pnm_test_type (DocsPnmCmCtlTest): Enum indicating the test type.
            filename (str): Name of the associated binary file.

        Returns:
            str: A unique transaction ID.
        """
        sd:SystemDescriptor = await cable_modem.getSysDescr()
        return self._insert_generic(mac_address=cable_modem.get_mac_address, 
                                 pnm_test_type=pnm_test_type, 
                                 filename=filename,
                                 sys_descriptor=sd.to_dict())

    @staticmethod
    def set_file_by_user(mac_address: MacAddress, pnm_test_type: DocsPnmCmCtlTest, filename: str) -> str:
        """
        Records a transaction manually initiated by a user (e.g., uploaded file).

        Args:
            mac_address (MacAddress): MAC address tied to the file.
            pnm_test_type (DocsPnmCmCtlTest): Enum for the associated test type.
            filename (str): The uploaded or externally generated file.

        Returns:
            str: The generated transaction ID.
        """
        txn = PnmFileTransaction()
        return txn._insert_generic(mac_address=mac_address, 
                                pnm_test_type=pnm_test_type, 
                                filename=filename)

    def get_record(self, transaction_id: str) -> Optional[dict]:
        """
        Retrieve metadata for a specified PNM file transaction.

        Example entry in the transaction database:
        {
            "<transaction_id>": {
                "timestamp": <ephoc>,
                "mac_address": "<cable modem mac address>",
                "pnm_test_type": "<PNM Test Type>",
                "filename": "<FileName>",
                "device_details": {
                    "sys_descr": sys_descriptor,
                }
            }
        }

        Args:
            transaction_id (str): 
                The 16-character transaction ID generated when the file was recorded.

        Returns:
            Optional[dict]: 
                A dict with the following keys if found:
                - `timestamp` (int): Epoch seconds when the file was created.
                - `mac_address` (str): Normalized MAC of the source cable modem.
                - `pnm_test_type` (str): Name of the PNM test enum used.
                - `filename` (str): Stored filename of the binary payload.
                Returns `None` if no entry exists for the given ID.

        Notes:
            - Corrupt or missing JSON DB files are treated as empty, so this method
            will simply return `None` rather than raising.
        """
        db = self._load_db()
        return db.get(transaction_id)

    def get_file_info_via_macaddress(self, mac_address: MacAddress) -> Optional[list[dict]]:
        """
        Searches the transaction database for all entries matching the given MAC address.

        Args:
            mac_address (MacAddress): The MAC address to search for.

        Returns:
            list[dict] | None: A list of transaction metadata including transaction_id, or None if no match is found.
        """
        db = self._load_db()
        mac_str = str(mac_address).lower()
        results = []

        for txn_id, record in db.items():
            if record.get("mac_address", "").lower() == mac_str:
                results.append({
                    "transaction_id": txn_id,
                    "pnm_test_type": record.get("pnm_test_type"),
                    "filename": record.get("filename"),
                    "timestamp": datetime.fromtimestamp(record.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "device_details": record.get("device_details","sys_descr"),
                })

        return results if results else None
   
    def _insert_generic(self, mac_address: MacAddress, 
                        pnm_test_type: DocsPnmCmCtlTest, 
                        filename: str, 
                        sys_descriptor:Dict[str,str]=SystemDescriptor.empty()) -> str: # type: ignore
        """
        Common logic for creating a transaction record.

        {
            "<transaction_id>": {
                "timestamp": <ephoc>,
                "mac_address": "<cable modem mac address>",
                "pnm_test_type": "<PNM Test Type>",
                "filename": "<FileName>",
                "device_details": {
                    "sys_descr": sys_descriptor,
                }
            }
        }

        Args:
            mac_address (MacAddress): MAC address associated with the record.
            pnm_test_type (DocsPnmCmCtlTest): Test type.
            filename (str): File name.

        Returns:
            str: A generated transaction ID.
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
                "sys_descr": sys_descriptor,
            }
        }
        self._save_db(db)
        return transaction_id

    def _load_db(self) -> dict:
        """
        Loads the transaction database from the configured JSON file.

        Returns:
            dict: Parsed JSON content or empty dict on failure.
        """
        try:
            with self.transaction_db_path.open("r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_db(self, db: dict):
        """
        Persists the transaction database to disk.

        Args:
            db (dict): The transaction dictionary to be saved.

        Raises:
            RuntimeError: If file saving fails.
        """
        try:
            with self.transaction_db_path.open("w") as f:
                json.dump(db, f, indent=4)
        except Exception as e:
            raise RuntimeError(f"Failed to save transaction DB: {e}")
