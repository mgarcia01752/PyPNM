# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum

class FileType(Enum):
    """
    Enumeration of supported file output types:

    - JSON: JavaScript Object Notation format (media type "application/json")
    - CSV: Comma-Separated Values format (media type "text/csv")
    - XLSX: Excel Open XML Spreadsheet format 
            (media type "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    - ARCHIVE: Aggregate archive format (e.g., ZIP) that may contain multiple file types 
               such as CSV, PNG, and other artifacts 
               (media type "application/zip")
    """
    JSON    = 0
    CSV     = 1
    XLSX    = 2
    ARCHIVE = 3

