# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pathlib import Path
from typing import List, Tuple
import logging

from pypnm.api.routes.advance.common.pnm_collection import PnmCollection
from pypnm.config.config_manager import ConfigManager
from pypnm.api.routes.common.classes.file_capture.capture_group import CaptureGroup
from pypnm.api.routes.common.classes.file_capture.pnm_file_transaction import PnmFileTransaction


class CaptureDataAggregator:
    """
    Generic class for collecting raw capture files based on a group ID.

    This class retrieves transaction IDs from a CaptureGroup, looks up file
    paths via PnmFileTransaction, and reads file contents.

    Usage:
        aggregator = CaptureDataAggregator(capture_group_id)
        file_entries = aggregator.collect()

    Attributes:
        capture_group_id (str): UUID grouping related captures.
        save_dir (Path): Directory where capture files are saved.
        logger (logging.Logger): Logger for warnings and errors.
    """

    def __init__(self, capture_group_id: str) -> None:
        """
        Initialize the aggregator for a specific capture group.

        Args:
            capture_group_id: Identifier for the capture group.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.capture_group_id = capture_group_id
        self.save_dir = Path(
            ConfigManager().get("PnmFileRetrieval", "save_dir")
        )

    def collect(self) -> List[Tuple[str, bytes]]:
        """
        Gather all capture files for the configured group and read their contents.

        Returns:
            List[Tuple[str, bytes]]: A list of tuples where each tuple is
                (filename, raw file bytes).

        Raises:
            FileNotFoundError: If a listed file does not exist.
        """
        group = CaptureGroup(group_id=self.capture_group_id)
        txn_ids = group.get_transactions()

        file_bin_entries: List[Tuple[str, bytes]] = []
        file_count = 1
        for txn in txn_ids:
            rec = PnmFileTransaction().get_record(txn)
            if not rec:
                self.logger.warning(f"No DB record for transaction '{txn}'")
                continue

            # Determine filename from record
            filename = None
            if hasattr(rec, 'filename'):
                filename = rec.filename # type: ignore
            elif isinstance(rec, dict):
                filename = rec.get('filename')

            if not filename:
                self.logger.warning(f"Transaction '{txn}' has no filename")
                continue
            
            self.logger.debug(f'Count: {file_count} - File: {filename}')
            file_count +=1
            
            file_path = self.save_dir / filename
            self.logger.info(f'Reading: {file_path}')
            try:
                content = file_path.read_bytes()
                file_bin_entries.append((filename, content))
            except FileNotFoundError:
                self.logger.error(f"Capture file not found: {file_path}")
                raise
            except Exception as exc:
                self.logger.error(f"Error reading file {file_path}: {exc}")
                continue
                        
        return file_bin_entries
    
    def getPnmCollection(self) -> PnmCollection:
        return PnmCollection(self.collect())
