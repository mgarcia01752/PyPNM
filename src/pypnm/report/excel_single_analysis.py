
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Optional
import os
from datetime import datetime

from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.file_capture.transaction_record_parser import TransactionRecordParser
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.lib.excel.excel_factory import ExcelWorkbookFactory
from pypnm.lib.file_processor import FileProcessor
from pypnm.pnm.process.fetch_pnm_process import PnmFileTypeObjectFetcher
from pypnm.pnm.process.pnm_file_type import PnmFileType


class ExcelSingleAnalysisReport:
    """
    Generates an Excel report based on a specific PNM file transaction ID.
    The report includes CM metadata, modulation summary, and per-channel RxMER data.
    """

    def __init__(self, transaction_id: str):
        """
        Initialize the report generator for a given transaction.

        Args:
            transaction_id: Unique ID identifying the PNM file transaction.

        Raises:
            ValueError: If no transaction record is found.
        """
        self.transaction_id = transaction_id
        self.trans_record = TransactionRecordParser(self.transaction_id)

    def _get_pnm_file(self) -> bytes:
        """
        Reads the binary content of the associated PNM file.

        Returns:
            bytes: The raw binary data of the PNM capture file.

        Raises:
            FileNotFoundError: If the expected file is missing.
        """
        save_dir = SystemConfigSettings.save_dir
        file_path = os.path.join(save_dir, self.trans_record.get_filename())

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"PNM file not found: {file_path}")

        return FileProcessor(file_path).read_file()

    def _get_analysis(self) -> ExcelWorkbookFactory:
        """
        Parses the file and performs RxMER analysis.
        Prepares an Excel workbook with metadata and carrier analysis.

        Returns:
            ExcelWorkbookFactory: A populated workbook ready to be saved.

        Raises:
            ValueError: If the file type is unsupported.
        """
        f = self._get_pnm_file()
        parser = PnmFileTypeObjectFetcher(f).get_parser()

        if parser.get_pnm_file_type() != PnmFileType.RECEIVE_MODULATION_ERROR_RATIO:
            raise ValueError("Unsupported PNM file type for Excel analysis.")

        # Run the RxMER analysis
        result = Analysis.basic_analysis_rxmer(parser.to_dict())
        workbook = ExcelWorkbookFactory()

        # Sheet 1: Device Info
        device_info = {
            "MAC Address": self.trans_record.get_mac_address(),
            "Model": self.trans_record.get_device_model(),
            "Vendor": self.trans_record.get_device_vendor(),
            "SW_REV": self.trans_record.get_software_revision(),
            "HW_REV": self.trans_record.get_hardware_revision(),
            "Test Type": self.trans_record.get_test_type(),
            "Timestamp": self.trans_record.get_timestamp(),
        }
        workbook.create_table("Device Info", [device_info])

        # Sheet 2: Modulation Summary
        summary_stats = result.get("modulation_statistics", {})
        mod_summary = [
            {"Modulation": mod, "Count": count}
            for mod, count in summary_stats.get("supported_modulation_counts", {}).items()
        ]
        if mod_summary:
            workbook.create_table("Modulation Summary", mod_summary)

        # Sheet 3+: Each OFDM channel (RxMER)
        carrier_channels = result.get("carrier_values", [])

        # Support backward compatibility with older RxMER structure
        if isinstance(carrier_channels, dict):
            carrier_channels = [carrier_channels]

        for idx, ch_data in enumerate(carrier_channels, start=1):
            freqs = ch_data.get("frequency", [])
            magnitudes = ch_data.get("magnitude", [])
            statuses = ch_data.get("carrier_status", [])

            if not freqs or not magnitudes:
                continue

            channel_rows = [
                {
                    "Subcarrier": i,
                    "Frequency (Hz)": freqs[i],
                    "RxMER (dB)": magnitudes[i],
                    "Status": statuses[i] if i < len(statuses) else None
                }
                for i in range(len(freqs))
            ]

            sheet_name = f"RxMER Channel {idx}"
            workbook.create_table(sheet_name, channel_rows)

        return workbook

    def generate_excel_report(self) -> str:
        """
        Creates and saves the Excel report.

        Returns:
            str: Full path to the generated Excel report.
        """
        workbook = self._get_analysis()

        # Filename: <testtype>_<mac>_<timestamp>.xlsx
        mac = self.trans_record.get_mac_address().replace(":", "")
        ts = datetime.fromtimestamp(self.trans_record.get_timestamp()).strftime("%Y%m%d_%H%M%S")
        test_type = self.trans_record.get_test_type().lower()
        filename = f"{test_type}_{mac}_{ts}.xlsx"

        output_dir = os.path.join(SystemConfigSettings.output_dir, "excel")
        os.makedirs(output_dir, exist_ok=True)

        full_path = os.path.join(output_dir, filename)
        workbook.save(full_path)
        return full_path
