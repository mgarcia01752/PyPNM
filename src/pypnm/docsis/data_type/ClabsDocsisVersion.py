from enum import IntEnum

class ClabsDocsisVersion(IntEnum):
    """
    Enum representing DOCSIS RF specification versions.

    Maps to the ClabsDocsisVersion textual convention used in SNMP MIBs.
    """
    OTHER = 0          # Unknown or unspecified
    DOCSIS_10 = 1      # DOCSIS 1.0
    DOCSIS_11 = 2      # DOCSIS 1.1
    DOCSIS_20 = 3      # DOCSIS 2.0
    DOCSIS_30 = 4      # DOCSIS 3.0
    DOCSIS_31 = 5      # DOCSIS 3.1
    DOCSIS_40 = 6      # DOCSIS 4.0

    def __str__(self):
        return self.name.replace("DOCSIS_", "DOCSIS ").replace("_", ".")
