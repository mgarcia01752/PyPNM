
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import IntEnum

class FileType(IntEnum):
    """
    Enumeration of supported file output types:

    - JSON: JavaScript Object Notation format (media type "application/json")
    - CSV: Comma-Separated Values format (media type "text/csv")
    - ARCHIVE: Aggregate archive format (e.g., ZIP) that may contain multiple file types 
               such as CSV, PNG, and other artifacts 
               (media type "application/zip")
    """
    JSON    = 0
    CSV     = 1
    ARCHIVE = 2

