# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

# from pypnm.api.routes.common.classes.analysis.analysis import Analysis   # < This is causing circular import noqa: F401 (reserved for future use)
from pypnm.api.routes.common.classes.file_capture.file_type import FileType
from pypnm.api.routes.common.classes.file_capture.pnm_file_transaction import PnmFileTransaction
from pypnm.api.routes.common.classes.file_capture.types import TransactionId
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.docsis.cm_snmp_operation import DocsPnmCmCtlTest
from pypnm.lib.archive.manager import ArchiveManager
from pypnm.lib.constants import MediaType
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import MacAddressStr, PathLike, TimeStamp
from pypnm.lib.utils import Utils
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader
from pypnm.pnm.process.pnm_type_header_mapper import PnmFileTypeMapper

from .schemas import (
    AnalysisResponse, FileAnalysisRequest, FileEntry, FileQueryRequest,
    FileQueryResponse, PushFileRequest, PushFileResponse,)


class PnmFileService:
    """
    Handles file storage, metadata registration, and high-level analysis
    for PNM-related binary data pushed into the PyPNM system.

    Methods:
        - search_files: List available files by MAC.
        - get_file_by_transaction_id: Download raw PNM file by transaction ID.
        - push_file: Accepts uploaded files, saves, and registers.
        - get_analysis: Produces analysis for a stored file.
        - get_file: Serve generated CSV/JSON/ARCHIVE files.
    """

    def __init__(self):
        self.pnm_dir = SystemConfigSettings.pnm_dir
        self.logger = logging.getLogger(self.__class__.__name__)

    def search_files(self, req: FileQueryRequest) -> FileQueryResponse:
        """
        Searches for all registered PNM files tied to a specific MAC address.
        """
        try:
            mac = MacAddress(req.mac_address)
            txn = PnmFileTransaction()
            results = txn.get_file_info_via_macaddress(mac)

            if not results:
                self.logger.warning(f"No files found for MAC: {mac}")
                return FileQueryResponse(files={str(mac): []})

            file_entries: list[FileEntry] = []

            for entry in results:
                device_details = getattr(entry, "device_details", None)

                if hasattr(device_details, "model_dump"):
                    # SystemDescriptorModel → plain dict
                    system_description = device_details.model_dump()
                elif isinstance(device_details, dict):
                    system_description = device_details
                else:
                    system_description = None

                file_entries.append(
                    FileEntry(
                        transaction_id      = entry.transaction_id,
                        filename            = entry.filename,
                        pnm_test_type       = entry.pnm_test_type,
                        timestamp           = entry.timestamp,
                        system_description  = system_description,
                    )
                )

            return FileQueryResponse(files={str(mac): file_entries})

        except Exception as e:
            self.logger.error(f"Failed to search files for MAC {req.mac_address}: {e}")
            return FileQueryResponse(files={req.mac_address: []})

    def get_file_by_transaction_id(self, transaction_id: TransactionId) -> FileResponse:
        """
        Retrieves and serves the binary file associated with the given transaction ID.
        """
        txn_data = PnmFileTransaction().get_record(transaction_id)

        if not txn_data:
            raise HTTPException(status_code=404, detail="Transaction ID not found.")

        filename = txn_data.get("filename")
        full_path = Path(self.pnm_dir) / str(filename)

        self.logger.info(f"Retrieving file for transaction {transaction_id}: {full_path}")

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk.")

        return FileResponse(
            path        =   full_path,
            filename    =   filename,
            media_type  =   MediaType.APPLICATION_OCTET_STREAM,
        )

    def get_file_by_mac_address(self, mac_address: MacAddressStr) -> FileResponse:
        """
        Retrieve All PNM Files For A MAC Address As A ZIP Archive.

        Looks up all transaction records bound to the provided cable modem
        MAC address, collects their associated PNM files from the PNM
        directory, and packages them into a single ZIP archive for download.

        If no records are found, or none of the files exist on disk, a 404 is raised.
        """
        records = PnmFileTransaction().get_file_info_via_macaddress(MacAddress(mac_address))

        if not records:
            raise HTTPException(status_code=404, detail="No transactions found for MAC address.")

        # Resolve all existing files for this MAC
        files_to_archive: list[Path] = []
        for rec in records:
            src_path = Path(self.pnm_dir) / Path(rec.filename)
            if not src_path.is_file():
                self.logger.warning(
                    "Skipping missing file for transaction %s: %s",
                    rec.transaction_id,
                    src_path,
                )
                continue
            files_to_archive.append(src_path)

        if not files_to_archive:
            raise HTTPException(status_code=404, detail="No files on disk for MAC address.")

        archive_dir = Path(SystemConfigSettings.archive_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)

        safe_mac = str(MacAddress(mac_address).to_mac_format())
        archive_name = f"pnm_files_{safe_mac}_{Utils.time_stamp()}.zip"
        archive_path = archive_dir / archive_name

        ArchiveManager.zip_files(
            files           = files_to_archive,
            archive_path    = archive_path,
            mode            = "w",
            compression     = "zipdeflated",
            preserve_tree   = False,
        )

        if not archive_path.is_file():
            self.logger.error("Archive creation failed for MAC %s at %s", mac_address, archive_path)
            raise HTTPException(status_code=500, detail="Failed to create archive for MAC address.")

        self.logger.info("Returning ZIP archive for MAC %s: %s", mac_address, archive_path)

        return FileResponse(
            path        =   str(archive_path),
            filename    =   archive_name,
            media_type  =   MediaType.APPLICATION_ZIP,
        )

    def upload_file(self, req: PushFileRequest) -> PushFileResponse:
        """
        Handles user-initiated uploads of raw PNM binary files.

        1. Saves the file locally to the configured directory.
        2. Inspects its header to identify the PNM file type.
        3. Maps it to a known DOCSIS test type.
        4. Registers the transaction and returns the transaction ID.
        """
        os.makedirs(self.pnm_dir, exist_ok=True)
        filepath = os.path.join(self.pnm_dir, req.filename)

        processor = FileProcessor(filepath)
        success = processor.write_file(req.data or "")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write file")

        header = PnmHeader(processor.read_file())
        pnm_file_type: PnmFileType = header.get_pnm_file_type()

        if not pnm_file_type:
            self.logger.error(f"Unrecognized PNM file format: {req.filename}")
            raise HTTPException(status_code=400, detail="Unsupported or unrecognized PNM file type.")

        test_type: DocsPnmCmCtlTest = PnmFileTypeMapper.get_test_type(pnm_file_type)
        if not test_type:
            self.logger.error(f"No mapping found from file type {pnm_file_type} to DOCSIS test")
            raise HTTPException(status_code=400, detail="PNM file type does not map to a known DOCSIS test")

        transaction_id = PnmFileTransaction().set_file_by_user(
            mac_address=MacAddress(req.mac_address),
            pnm_test_type=test_type,
            filename=req.filename,
        )

        return PushFileResponse(
            mac_address     =   req.mac_address,
            filename        =   req.filename,
            transaction_id  =   transaction_id,
        )

    def get_analysis(self, req: FileAnalysisRequest) -> AnalysisResponse:
        """
        Returns basic analysis result for a stored file (placeholder implementation).

        Currently resolves the filename from the transaction ID and returns a
        stubbed plot URL; analysis orchestration will be wired in later.
        """
        txn_data = PnmFileTransaction().get_record(req.transaction_id)
        if not txn_data:
            raise HTTPException(status_code=404, detail="Transaction ID not found for analysis.")

        filename = str(txn_data.get("filename", "unknown"))
        safe_stem = Path(filename).stem

        return AnalysisResponse(
            analysis_type=req.analysis_type or "auto",
            plot_url=f"/static/plots/{safe_stem}.png",
            summary=f"Auto analysis placeholder for transaction {req.transaction_id}",
        )

    def get_file(self, file_type: FileType, filename: PathLike) -> FileResponse:
        """
        Serve a generated file from its configured directory.

        Supported types:
        - CSV: returns text/csv from SystemConfigSettings.csv_dir
        - JSON: returns application/json from SystemConfigSettings.json_dir
        - ARCHIVE: returns application/zip from SystemConfigSettings.archive_dir
        """
        safe_name = Path(filename).name

        valid_extensions = [".csv", ".json", ".zip"]
        if not any(safe_name.endswith(ext) for ext in valid_extensions):
            raise HTTPException(status_code=400, detail=f"Invalid file extension, file: {safe_name}")

        if file_type == FileType.CSV:
            base_dir = SystemConfigSettings.csv_dir
            media_type = MediaType.TEXT_CSV

        elif file_type == FileType.JSON:
            base_dir = SystemConfigSettings.json_dir
            media_type = MediaType.APPLICATION_JSON

        elif file_type == FileType.ARCHIVE:
            base_dir = SystemConfigSettings.archive_dir
            media_type = MediaType.APPLICATION_ZIP

        else:
            self.logger.error(f"Unsupported file type requested: {file_type.name}")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type.name}")

        file_path = Path(base_dir) / safe_name
        if not file_path.is_file():
            self.logger.warning(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found on disk.")

        return FileResponse(
            path        =   str(file_path),
            filename    =   safe_name,
            media_type  =   media_type,
        )
