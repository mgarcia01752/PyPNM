from enum import Enum

class FileType(Enum):
    """
    Enumeration of supported file output types:

    - JSON: JavaScript Object Notation format (media type "application/json")
    - CSV: Comma-Separated Values format (media type "text/csv")
    - XLSX: Excel Open XML Spreadsheet format (media type "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    """
    JSON = 0
    CSV  = 1
    XLSX = 2
