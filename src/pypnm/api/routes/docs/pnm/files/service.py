# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException
from fastapi.responses import FileResponse

from pypnm.api.routes.common.classes.file_capture.file_type import FileType
from pypnm.api.routes.common.classes.file_capture.pnm_file_transaction import PnmFileTransaction
from pypnm.api.routes.common.classes.file_capture.types import TransactionId, TransactionRecordModel
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.lib.archive.manager import ArchiveManager
from pypnm.lib.constants import MediaType
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.types import MacAddressStr, PathLike
from pypnm.lib.utils import Utils
from pypnm.pnm.process.fetch_pnm_process import PnmFileTypeObjectFetcher, PnmParserClass
from pypnm.pnm.process.pnm_header import PnmHeader
from pypnm.pnm.process.pnm_type_header_mapper import PnmFileTypeMapper

from .schemas import (FileQueryRequest, UploadFileRequest, FileQueryResponse,
                      UploadFileResponse, AnalysisResponse)

class PnmFileService:
    """
    Handles file storage, metadata registration, and high-level analysis
    for PNM-related binary data pushed into the PyPNM system.

    Methods:
        - search_files: List available files by MAC.
        - upload_file: Accepts uploaded files into a temporary area and registers them.
        - get_analysis: One-shot upload + analysis flow (development stub for now).
        - get_file_by_transaction_id: Download a file by transaction id.
        - get_file_by_macaddress: Zip and download all files for a MAC.
        - get_file_by_filename: Download a file by name from the persistent PNM area.
        - get_file: Download generated CSV/JSON/ZIP artifacts.
    """

    def __init__(self):
        self.pnm_dir = SystemConfigSettings.pnm_dir
        self.logger  = logging.getLogger(self.__class__.__name__)

    def search_files(self, request: FileQueryRequest) -> FileQueryResponse:
        """
        Search Registered PNM Transactions For A Given MAC Address.

        This method normalizes the supplied MAC address, queries the
        transaction database via `PnmFileTransaction`, and returns all
        matching entries as `TransactionRecordModel` instances grouped
        under the normalized MAC key.

        Typical usage includes:
        - Populating UI tables of all known PNM captures for a modem.
        - Providing selection lists for downstream download or analysis.
        - Inspecting historical file inventory for troubleshooting.

        Parameters
        ----------
        request:
            Request payload containing the target cable modem details,
            including the MAC address used for the lookup.

        Returns
        -------
        FileQueryResponse
            Response object whose `files` mapping uses the normalized MAC
            address string as the key and a list of `TransactionRecordModel`
            instances as the value. If no transactions exist for the MAC,
            the list is empty.
        """
        try:
            mac = MacAddress(request.mac_address)
        except ValueError as exc:
            self.logger.warning("Invalid MAC address provided for search: %s", getattr(request, "mac_address", None))
            raise HTTPException(status_code=400, detail="Invalid MAC address format") from exc

        try:
            txn     = PnmFileTransaction()
            records = txn.get_file_info_via_macaddress(mac)

            if not records:
                self.logger.info("No PNM file transactions found for MAC %s", mac)
                return FileQueryResponse(files={str(mac): []})

            typed_records: list[TransactionRecordModel] = list(records)
            return FileQueryResponse(files={str(mac): typed_records})

        except HTTPException:
            raise
        except Exception as exc:
            self.logger.error("Failed to search files for MAC %s: %s", mac, exc)
            return FileQueryResponse(files={str(mac): []})

    def get_file_by_transaction_id(self, transaction_id: TransactionId) -> FileResponse:
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
        if not filename:
            raise HTTPException(status_code=404, detail="Transaction record missing filename.")

        filename_path = Path(str(filename))
        if filename_path.is_absolute():
            full_path = filename_path
        else:
            full_path = Path(self.pnm_dir) / filename_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk.")

        return FileResponse(path=str(full_path), filename=full_path.name, media_type="application/octet-stream")

    def upload_file(self, req: UploadFileRequest) -> UploadFileResponse:
        """
        Handle User-Initiated Upload Of A Raw PNM Binary File Into A Temporary Area.

        This is a thin wrapper around `__upload_file` that performs the actual
        upload, header inspection, PNM type classification, parser construction,
        and transaction registration. The on-disk file is placed under a
        dedicated temporary upload root:

            /tmp/pypnm_uploads/<filename>

        The permanent PNM capture directory (`pnm_dir`) is not modified by this
        method. The transaction record stores the absolute temp-file path so that
        later analysis stages can locate it unambiguously.

        Parameters
        ----------
        req:
            Upload request containing the target filename and binary payload.

        Returns
        -------
        UploadFileResponse
            Lightweight response containing the canonical filename and the
            registered transaction identifier.
        """
        upload_response, _1, _2 = self.__upload_file(req)
        return upload_response

    def __upload_file(self, req: UploadFileRequest) -> Tuple[UploadFileResponse, Path, PnmParserClass]:
        """
        Core Upload Logic For PNM Files Backed By The Temporary Upload Root.

        Steps:
        1. Ensure `SystemConfigSettings.pnm_dir` exists.
        2. Write the uploaded payload to `SystemConfigSettings.pnm_dir/<filename>`.
        3. Parse the PNM header to determine `PnmFileType`.
        4. Map the file type to a DOCSIS test type (`DocsPnmCmCtlTest`).
        5. Build a PNM parser via `PnmFileTypeObjectFetcher` and extract its model.
        6. Register a transaction using the decoded `mac_address` from the model.
        7. Return the `UploadFileResponse` plus the absolute on-disk path.

        Parameters
        ----------
        req:
            Upload request containing the target filename and binary payload.

        Returns
        -------
        Tuple[UploadFileResponse, Path]
            The structured upload response and the absolute file path on disk.

        Raises
        ------
        HTTPException
            - 500 if the file cannot be written.
            - 400 if the PNM file type is unsupported or cannot be mapped to a test.
        """
        pnm_dir = Path(SystemConfigSettings.pnm_dir)
        pnm_dir.mkdir(parents=True, exist_ok=True)

        safe_name = Path(req.filename).name
        filepath  = pnm_dir / safe_name
        processor = FileProcessor(filepath)
        success   = processor.write_file(req.data or b"")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write uploaded PNM file")

        raw_bytes = processor.read_file()
        if not raw_bytes:
            self.logger.error("Uploaded PNM file is empty: %s", filepath)
            raise HTTPException(status_code=400, detail="Uploaded PNM file is empty or unreadable")

        header = PnmHeader(raw_bytes)
        pnm_file_type = header.get_pnm_file_type()

        if not pnm_file_type:
            self.logger.error("Unrecognized PNM file format: %s", safe_name)
            raise HTTPException(status_code=400, detail="Unsupported or unrecognized PNM file type.")

        test_type = PnmFileTypeMapper.get_test_type(pnm_file_type)
        if not test_type:
            self.logger.error("No mapping found from file type %s to DOCSIS test", pnm_file_type)
            raise HTTPException(status_code=400, detail="PNM file type does not map to a known DOCSIS test")

        parser = PnmFileTypeObjectFetcher(raw_bytes).get_parser()
        pnm_obj_model = parser.to_model()
        mac = MacAddress(getattr(pnm_obj_model, "mac_address", MacAddress.null()))

        if mac.is_null():
            self.logger.error("Uploaded PNM file missing valid MAC address: %s", safe_name)
            raise HTTPException(status_code=400, detail="PNM file missing valid MAC address in header") 

        transaction_id = PnmFileTransaction().set_file_by_user(
            mac_address   = mac,
            pnm_test_type = test_type,
            filename      = safe_name,
        )

        return (
            UploadFileResponse(
                filename       = safe_name,
                transaction_id = transaction_id,
            ),
            filepath,
            parser,
        )

    def get_analysis(self, req: UploadFileRequest) -> AnalysisResponse:
        """
        One-Shot Upload And Basic Analysis Placeholder For A PNM File.

        This development stub performs an inline upload using the same logic
        as `upload_file`, then returns a minimal `AnalysisResponse` that is
        tied to the uploaded file.

        The current implementation:
        - Writes the file under `/tmp/pypnm_uploads`.
        - Registers a transaction keyed by the decoded MAC address.
        - Returns a canned analysis response referencing a hypothetical plot
          location derived from the uploaded filename.

        Parameters
        ----------
        req:
            Upload request containing the filename, payload, and (optionally)
            an `analysis_type` attribute if present on the request model.

        Returns
        -------
        AnalysisResponse
            Placeholder analysis result referencing the uploaded PNM file.
        """
        upload_response, target_path, parser_class = self.__upload_file(req)
        safe_name   = target_path.name
        analysis_ty = getattr(req, "analysis_type", "auto") or "auto"

        return AnalysisResponse(
            analysis_type = analysis_ty,
            plot_url      = f"/static/plots/{safe_name}.png",
            summary       = f"Auto analysis placeholder for transaction {upload_response.transaction_id}",
        )

    def get_file(self, file_type: FileType, filename: PathLike) -> FileResponse:
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
        valid_extensions = ['.csv', '.json', '.zip']
        if not any(safe_name.endswith(ext) for ext in valid_extensions):
            raise HTTPException(status_code=400, detail=f"Invalid file extension, file: {safe_name}")

        # Choose directory and media type per FileType
        if file_type == FileType.CSV:
            base_dir   = SystemConfigSettings.csv_dir
            media_type = MediaType.TEXT_CSV

        elif file_type == FileType.JSON:
            base_dir   = SystemConfigSettings.json_dir
            media_type = MediaType.APPLICATION_JSON
                
        elif file_type == FileType.ARCHIVE:
            base_dir   = SystemConfigSettings.archive_dir
            media_type = MediaType.APPLICATION_ZIP
                       
        else:
            self.logger.error(f"Unsupported file type requested: {file_type.name}")
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type.name}")

        file_path = Path(base_dir) / safe_name
        if not file_path.is_file():
            self.logger.warning(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail="File not found on disk.")

        return FileResponse(
            path     = str(file_path),
            filename = safe_name,
            media_type = media_type,
        )

    def get_file_by_macaddress(self, mac_address: MacAddressStr) -> FileResponse:
        """
        Build And Download A ZIP Archive Of All PNM Files For A Given MAC Address.

        This method aggregates every transaction associated with the supplied
        MAC address, locates the corresponding PNM files (either under the
        persistent `pnm_dir` or using absolute paths stored in the transaction
        record), and packages the existing files into a single ZIP archive
        under the configured `archive_dir`.

        Parameters
        ----------
        mac_address:
            MAC address of the cable modem whose PNM files should be bundled.

        Returns
        -------
        FileResponse
            HTTP response streaming the generated ZIP archive containing all
            available PNM files tied to the specified MAC address.

        Raises
        ------
        HTTPException
            - 400 if the MAC address format is invalid.
            - 404 if no transactions are found or none of the referenced
              PNM files exist on disk.
        """
        try:
            mac = MacAddress(mac_address)
        except ValueError as exc:
            self.logger.warning("Invalid MAC address provided for archive: %s", mac_address)
            raise HTTPException(status_code=400, detail="Invalid MAC address format") from exc

        txn     = PnmFileTransaction()
        records = txn.get_file_info_via_macaddress(mac)

        if not records:
            self.logger.info("No PNM file transactions found for MAC %s", mac)
            raise HTTPException(status_code=404, detail="No PNM transactions found for MAC address.")

        pnm_root    = Path(self.pnm_dir)
        archive_dir = Path(SystemConfigSettings.archive_dir)
        archive_dir.mkdir(parents=True, exist_ok=True)

        safe_mac   = mac.mac_address
        archive_fn = f"pnm_files_{safe_mac}_{Utils.time_stamp()}.zip"
        archive_fp = archive_dir / archive_fn

        files_to_archive: list[Path] = []
        for record in records:
            filename_path = Path(str(record.filename))
            if filename_path.is_absolute():
                full_path = filename_path
            else:
                full_path = pnm_root / filename_path

            if full_path.is_file():
                files_to_archive.append(full_path)
            else:
                self.logger.warning("PNM file missing for transaction %s: %s", record.transaction_id, full_path)

        if not files_to_archive:
            self.logger.warning("All referenced PNM files are missing for MAC %s", mac)
            raise HTTPException(status_code=404, detail="No PNM files found on disk for MAC address.")

        ArchiveManager.zip_files(
            files         = files_to_archive,
            archive_path  = archive_fp,
            mode          = "w",
            compression   = "zipdeflated",
            preserve_tree = False,
        )

        return FileResponse(
            path     = archive_fp,
            filename = archive_fn,
            media_type = MediaType.APPLICATION_ZIP,
        )

    def get_file_by_filename(self, filename: PathLike) -> FileResponse:
        """
        Retrieve And Serve A Raw PNM File By Its Filename.

        This method constructs the on-disk path for the requested PNM file
        using the configured `pnm_dir` and the basename of the provided
        filename. If the file exists, it is returned as a binary
        `FileResponse` suitable for direct download.

        Typical usage includes:
        - Downloading a specific PNM capture when the filename is already known.
        - Integrations where the UI passes back a previously listed filename.
        - Simple file retrieval workflows that do not require transaction IDs.

        Parameters
        ----------
        filename:
            Filename of the PNM capture to download. Any directory components
            are stripped and only the basename is used under `pnm_dir`.

        Returns
        -------
        FileResponse
            HTTP response streaming the requested PNM file to the client.

        Raises
        ------
        HTTPException
            - 404 if the file does not exist on disk.
        """
        safe_name = Path(filename).name
        full_path = Path(self.pnm_dir) / safe_name

        if not full_path.is_file():
            self.logger.warning("PNM file not found by filename: %s", full_path)
            raise HTTPException(status_code=404, detail="PNM file not found on disk.")

        return FileResponse(
            path     = str(full_path),
            filename = safe_name,
            media_type = MediaType.APPLICATION_OCTET_STREAM,
        )
