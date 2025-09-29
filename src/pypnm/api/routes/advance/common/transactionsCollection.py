# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import Field

from pypnm.api.routes.advance.common.types.types import Sort
from pypnm.api.routes.common.classes.file_capture.types import TransactionId, TransactionRecordModel
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import ByteArray, MacAddressStr


class TransactionCollectionModel(TransactionRecordModel):
    """
    Extended transaction record model that includes raw file bytes.

    Attributes
    ----------
    data : bytes
        Capture data payload for the associated transaction file.
    """
    data: bytes = Field(..., description="(PNM/PNN/LDD) file bytes")


class TransactionCollection:
    """
    Collection container for handling transaction records, supporting sorting,
    retrieval by ID, and bulk operations.
    """

    def __init__(self) -> None:
        """
        Initialize internal storage for transaction records and indices.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self._records: List[TransactionCollectionModel] = []
        self._transaction_ids: List[TransactionId] = []
        self._transaction_models: List[TransactionCollectionModel] = []
        self._transaction_tm: Dict[TransactionId, TransactionCollectionModel] = {}
        self._tranaction_tm = self._transaction_tm  # alias
        self._mac_addresses:Set[MacAddress] = set()

    def add(self, record: TransactionRecordModel, bytes: bytes) -> bool:
        """
        Add a new transaction record and its associated data payload.

        Parameters
        ----------
        record : TransactionRecordModel
            Metadata describing the transaction.
        bytes : bytes
            Raw file contents.

        Returns
        -------
        bool
            True if added successfully.
        """
        tcm = TransactionCollectionModel(
            transaction_id  =   record.transaction_id,
            timestamp       =   record.timestamp,
            mac_address     =   record.mac_address,
            pnm_test_type   =   record.pnm_test_type,
            filename        =   record.filename,
            device_details  =   record.device_details,
            data            =   bytes,
        )
        self._records.append(tcm)
        self._transaction_tm[record.transaction_id] = tcm
        self._transaction_models.append(tcm)
        self._transaction_ids.append(record.transaction_id)
        self._mac_addresses.add(MacAddress(record.mac_address))
        return True

    def length(self) -> int:
        """
        Get the total number of transaction records in the collection.

        Returns
        -------
        int
            Count of records.
        """
        return len(self._records)

    def getTransactionIds(self, sorts: Optional[List[Sort]] = None, reverse: bool = False) -> List[TransactionId]:
        """
        Retrieve transaction IDs, optionally sorted.

        Parameters
        ----------
        sorts : list of Sort, optional
            Sorting priorities in order. If None, insertion order is used.
        reverse : bool
            If True, reverse the sorting order.

        Returns
        -------
        list of TransactionId
            Sorted list of transaction IDs.

        Raises
        ------
        ValueError
            If Sort.CHANNEL_ID is included in sorts.
        """
        if not sorts:
            return list(self._transaction_ids)
        sorted_records = self._sorted_records(sorts, reverse)
        return [r.transaction_id for r in sorted_records]

    def getTransactionCollectionModel(self, transaction_id: TransactionId = "", 
                                      sorts: Optional[List[Sort]] = None, 
                                      reverse: bool = False) -> List[TransactionCollectionModel]:
        """
        Retrieve transaction models by ID or sorted collection.

        Parameters
        ----------
        transaction_id : TransactionId, optional
            Specific transaction ID to retrieve. Returns all if empty.
        sorts : list of Sort, optional
            Sorting priorities in order.
        reverse : bool
            If True, reverse the sorting order.

        Returns
        -------
        list of TransactionCollectionModel
            Matching transaction models.
        """
        if transaction_id:
            model = self._transaction_tm.get(transaction_id)
            return [model] if model else []
        if not sorts:
            return list(self._transaction_models)
        return self._sorted_records(sorts, reverse)

    def getTransactionBytes(self, transaction_id: TransactionId = "", 
                            sorts: Optional[List[Sort]] = None, 
                            reverse: bool = False) -> ByteArray:
        """
        Retrieve raw data bytes from transactions.

        Parameters
        ----------
        transaction_id : TransactionId, optional
            Specific transaction ID to retrieve. Returns all if empty.
        sorts : list of Sort, optional
            Sorting priorities in order.
        reverse : bool
            If True, reverse the sorting order.

        Returns
        -------
        ByteArray
            List of raw data bytes from the matching transactions.
        """
        ba: ByteArray = []

        if transaction_id:
            tcm = self._transaction_tm.get(transaction_id)
            if tcm:
                ba.append(tcm.data)
            return ba

        records = self._sorted_records(sorts, reverse) if sorts else self._transaction_models
        for tcm in records:
            ba.append(tcm.data)
        return ba

    def getMacAddresses(self) -> List[MacAddress]:
        return list(self._mac_addresses)

    def _sorted_records(self, sorts: List[Sort], reverse: bool) -> List[TransactionCollectionModel]:
        """
        Internal helper to sort records based on provided sort keys.

        Parameters
        ----------
        sorts : list of Sort
            Sorting priorities in order.
        reverse : bool
            If True, reverse the sorting order.

        Returns
        -------
        list of TransactionCollectionModel
            Sorted records.

        Raises
        ------
        ValueError
            If Sort.CHANNEL_ID is included in sorts.
        """
        if Sort.CHANNEL_ID in sorts:
            raise ValueError("Sorting by CHANNEL_ID is not supported.")

        key_fn = self._composite_key_for_sorts(sorts)
        return sorted(self._records, key=key_fn, reverse=reverse)

    def _composite_key_for_sorts(self, sorts: List[Sort]):
        """
        Build a composite key function for multi-level sorting.

        Parameters
        ----------
        sorts : list of Sort
            Sorting priorities in order.

        Returns
        -------
        callable
            A key function for sorting.
        """
        def key(r: TransactionCollectionModel):
            parts: List[object] = []

            for s in sorts:
                if s == Sort.ASCEND_EPOCH:
                    parts.append(r.timestamp)
                elif s == Sort.MAC_ADDRESS:
                    parts.append(r.mac_address)
                elif s == Sort.PNM_FILE_TYPE:
                    parts.append(self._file_ext(r.filename))

            parts.append(r.transaction_id)
            return tuple(parts)

        return key

    @staticmethod
    def _file_ext(filename: str) -> str:
        """
        Extract file extension in lowercase without the leading dot.

        Parameters
        ----------
        filename : str
            Name of the file.

        Returns
        -------
        str
            File extension or empty string if none found.
        """
        return Path(filename).suffix.lower().lstrip(".")
