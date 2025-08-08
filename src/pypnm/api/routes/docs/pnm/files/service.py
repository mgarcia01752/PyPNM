# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import os
import logging
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

from pypnm.api.routes.common.classes.file_capture.file_type import FileType
from pypnm.api.routes.common.classes.file_capture.pnm_file_transaction import PnmFileTransaction
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.docsis.cm_snmp_operation import DocsPnmCmCtlTest
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.file_processor import FileProcessor
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader
from pypnm.pnm.process.pnm_type_header_mapper import PnmFileTypeMapper

from .schemas import (
    FileEntry,
    FileQueryRequest,
    PushFileRequest,
    FileAnalysisRequest,
    FileQueryResponse,
    PushFileResponse,
    AnalysisResponse
)

class PnmFileService:
    """
    Handles file storage, metadata registration, and high-level analysis
    for PNM-related binary data pushed into the PyPNM system.

    Methods:
        - get_files: List available files by MAC.
        - push_file: Accepts uploaded files, saves, and registers.
        - get_analysis: Produces analysis for a stored file.
    """

    def __init__(self):
        self.save_dir = SystemConfigSettings.save_dir
        self.logger = logging.getLogger(self.__class__.__name__)

    def search_files(self, req: FileQueryRequest) -> FileQueryResponse:
        """
        Searches for all registered PNM files tied to a specific MAC address.

        Args:
            req (FileQueryRequest): Request containing a MAC address.

        Returns:
            FileQueryResponse: A mapping of MAC address -> list of file metadata.
        """
        try:
            mac = MacAddress(req.mac_address)
            txn = PnmFileTransaction()
            results = txn.get_file_info_via_macaddress(mac)

            if not results:
                self.logger.warning(f"No files found for MAC: {mac}")
                return FileQueryResponse(files={str(mac): []})

            file_entries = []
            for entry in results:
                print(entry)
                file_entries.append(
                    FileEntry(
                        transaction_id=entry["transaction_id"],
                        filename=entry["filename"],
                        pnm_test_type=entry["pnm_test_type"],
                        timestamp=entry["timestamp"],
                        sys_descr=entry["device_details"]["sys_descr"]
                    )
                )

            return FileQueryResponse(files={str(mac): file_entries})

        except Exception as e:
            self.logger.error(f"Failed to search files for MAC {req.mac_address}: {e}")
            return FileQueryResponse(files={req.mac_address: []})

    def get_file_by_transaction_id(self, transaction_id: str) -> FileResponse:
        """
        Retrieves and serves the binary file associated with the given transaction ID.

        Args:
            transaction_id (str): The unique transaction ID for the file.

        Returns:
            FileResponse: The file served for download.
        """
        txn_data = PnmFileTransaction().get_record(transaction_id)

        if not txn_data:
            raise HTTPException(status_code=404, detail="Transaction ID not found.")

        filename = txn_data.get("filename")
        full_path = Path(self.save_dir) / str(filename)

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk.")

        return FileResponse(path=full_path, filename=filename, media_type='application/octet-stream')
    
    def push_file(self, req: PushFileRequest) -> PushFileResponse:
        """
        Handles user-initiated uploads of raw PNM binary files.

        1. Saves the file locally to the configured directory.
        2. Inspects its header to identify the PNM file type.
        3. Maps it to a known DOCSIS test type.
        4. Registers the transaction and returns the transaction ID.

        Raises:
            HTTPException if the file cannot be saved or type is unrecognized.
        """
        os.makedirs(self.save_dir, exist_ok=True)
        filepath = os.path.join(self.save_dir, req.filename)

        processor = FileProcessor(filepath)
        success = processor.write_file(req.data or "")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write file")

        header = PnmHeader(processor.read_file())
        pnm_file_type: PnmFileType = header.get_pnm_file_type() # type: ignore

        if not pnm_file_type:
            self.logger.error(f"Unrecognized PNM file format: {req.filename}")
            raise HTTPException(status_code=400, detail="Unsupported or unrecognized PNM file type.")

        test_type: DocsPnmCmCtlTest = PnmFileTypeMapper.get_test_type(pnm_file_type) # type: ignore
        if not test_type:
            self.logger.error(f"No mapping found from file type {pnm_file_type} to DOCSIS test")
            raise HTTPException(status_code=400, detail="PNM file type does not map to a known DOCSIS test")

        transaction_id = PnmFileTransaction().set_file_by_user(
            mac_address=MacAddress(req.mac_address),
            pnm_test_type=test_type,
            filename=req.filename
        )

        return PushFileResponse(
            mac_address=req.mac_address,
            filename=req.filename,
            transaction_id=transaction_id
        )

    def get_analysis(self, req: FileAnalysisRequest) -> AnalysisResponse:
        """
        Returns basic analysis result for a stored file (e.g., preview, plot).

        Args:
            req (FileAnalysisRequest): Filename and analysis type.

        Returns:
            AnalysisResponse: Summary, plot path, or inline results.
        """
        return AnalysisResponse(
            analysis_type=req.analysis_type or "auto",
            plot_url=f"/static/plots/{req.filename}.png",
            summary="Auto analysis complete"
        )

    def get_file(self, file_type: FileType, filename: str) -> FileResponse:
        """
        Serve a generated file from its configured directory.

        Supported types:
        - CSV: returns text/csv from SystemConfigSettings.csv_dir
        - JSON: returns application/json from SystemConfigSettings.json_dir
        - XLSX: returns Excel OpenXML from SystemConfigSettings.xlsx_dir

        Raises:
        - HTTPException 400 if the file_type is unsupported
        - HTTPException 404 if the file does not exist on disk
        """
        # Prevent directory traversal
        safe_name = Path(filename).name

        # Optional: Further sanitize the filename, ensure it's safe and has a valid extension.
        valid_extensions = ['.csv', '.json', '.xlsx']
        if not any(safe_name.endswith(ext) for ext in valid_extensions):
            raise HTTPException(status_code=400, detail="Invalid file extension.")
        
        # Choose directory and media type per FileType
        if file_type == FileType.CSV:
            base_dir = SystemConfigSettings.csv_dir
            media_type = "text/csv"

        elif file_type == FileType.JSON:
            base_dir = SystemConfigSettings.json_dir
            media_type = "application/json"
        
        elif file_type == FileType.XLSX:
            base_dir = SystemConfigSettings.xlsx_dir
            media_type = (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet")
        
        elif file_type == FileType.ARCHIVE:
            base_dir = SystemConfigSettings.zip_dir
            media_type = "application/zip"
                       
        else:
            self.logger.error(f"Unsupported file type requested: {file_type.name}")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type.name}")

        file_path = Path(base_dir) / safe_name
        if not file_path.is_file():
            self.logger.warning(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found on disk.")

        return FileResponse(
            path=str(file_path),
            filename=safe_name,
            media_type=media_type
        )
