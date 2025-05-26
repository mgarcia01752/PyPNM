# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
import struct
from typing import Any, Dict, Optional

from pnm.process.pnm_file_type import PnmFileType

class PnmHeader:
    def __init__(self, byte_array):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.file_type = None
        self.major_version:int = None
        self.minor_version:int = None
        self.capture_time:int = 0
        self.pnm_data:bytes = None
        
        self.__parse_header(byte_array)

    def __parse_header(self, byte_array):
        
        pnm_special_case = struct.unpack('<B', byte_array[3:4])
            
        if pnm_special_case[0] == 8:
            
            header_format = '<3sBBB'
            header_size = struct.calcsize(header_format)
            header_data = struct.unpack(header_format, byte_array[:header_size])
            
            self.file_type = header_data[0]
            self.file_type_num = header_data[1]
            self.major_version = header_data[2]
            self.minor_version = header_data[3]
        
        else:
            header_format = '!3sBBBI'
            header_size = struct.calcsize(header_format)
            header_data = struct.unpack(header_format, byte_array[:header_size])
            
            self.file_type = header_data[0]
            self.file_type_num = header_data[1]
            self.major_version = header_data[2]
            self.minor_version = header_data[3]
            self.capture_time = header_data[4]

        self.pnm_data:bytes = byte_array[header_size:]

    def getPnmHeader(self, header_only: bool = False) -> Dict[str, Any]:
        """
        Returns the PNM header information as a dictionary.

        Args:
            header_only (bool): If True, excludes the 'Data' field from the result.

        Returns:
            Dict[str, Any]: Dictionary containing parsed PNM header fields.
            
        header = {
            "pnm_header": {
            "file_type": self.file_type.decode('utf-8'),
            "file_type_version": self.file_type_num,
            "major_version": self.major_version,
            "minor_version": self.minor_version,
            "capture_time": self.capture_time,
            }
        }            
            
        """
        header = {
            "pnm_header": {
            "file_type": self.file_type.decode('utf-8'),
            "file_type_version": self.file_type_num,
            "major_version": self.major_version,
            "minor_version": self.minor_version,
            "capture_time": self.capture_time,
            }
        }

        if not header_only:
            header["data"] = self.pnm_data.hex()

        return header

    def get_pnm_file_type(self) -> Optional[PnmFileType]:
        """
        Attempts to map the combined file_type + file_type_num (e.g., 'PNN10') to a known `PnmFileType` enum.

        Returns:
            Optional[PnmFileType]: The matching enum value if found; otherwise, None.
        """
        try:
            if self.file_type and self.file_type_num is not None:

                pnm_id = f"{self.file_type.decode('utf-8').strip()}{self.file_type_num}"

                for pnm_type in PnmFileType:
                    if pnm_type.value == pnm_id:
                        return pnm_type

                self.logger.warning(f"Unrecognized PNM file type ID: {pnm_id}")
            else:
                self.logger.warning("Incomplete header: file_type or file_type_num is missing.")
        except Exception as e:
            self.logger.error(f"Error determining PNM file type: {e}")

        return None