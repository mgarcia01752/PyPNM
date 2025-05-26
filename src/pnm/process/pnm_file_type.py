# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum


class PnmFileType(Enum):
    """
    Enumeration of PNM file types, mapping human-readable names to
    4-character PNM CANN codes used in DOCSIS modem telemetry.

    Attributes:
        pnm_cann (str): The PNM CANN code identifying this file type.

    Methods:
        get_pnm_cann(): Return the raw PNM CANN code.
        to_ascii(): Alias for get_pnm_cann (returns ASCII code).
        from_name(name): Class method to lookup an enum by its name.
    """
    SYMBOL_CAPTURE                         = "PNN1"
    OFDM_CHANNEL_ESTIMATE_COEFFICIENT      = "PNN2"
    DOWNSTREAM_CONSTELLATION_DISPLAY       = "PNN3"
    RECEIVE_MODULATION_ERROR_RATIO         = "PNN4"
    DOWNSTREAM_HISTOGRAM                   = "PNN5"
    UPSTREAM_PRE_EQUALIZER_COEFFICIENTS    = "PNN6"
    UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE  = "PNN7"
    OFDM_FEC_SUMMARY                       = "PNN8"
    SPECTRUM_ANALYSIS                      = "PNN9"
    OFDM_MODULATION_PROFILE                = "PNN10"
    LATENCY_REPORT                         = "LLD01"

    def __init__(self, pnm_cann: str) -> None:
        """
        Initialize the enum member with its PNM CANN code.

        Args:
            pnm_cann (str): 4-character code used by the modem.
        """
        self.pnm_cann: str = pnm_cann

    def get_pnm_cann(self) -> str:
        """
        Retrieve the raw PNM CANN code for this file type.

        Returns:
            str: The 4-character PNM CANN identifier.
        """
        return self.pnm_cann

    def to_ascii(self) -> str:
        """
        Convert the PNM CANN code to its ASCII representation.

        Alias for `get_pnm_cann()`; provided for semantic clarity.

        Returns:
            str: ASCII string of the PNM code.
        """
        return self.get_pnm_cann()

    @classmethod
    def from_name(cls, name: str) -> 'PnmFileType':
        """
        Lookup a PnmFileType by its enum member name.

        Args:
            name (str): The enum member name (e.g., "SYMBOL_CAPTURE").

        Returns:
            PnmFileType: Corresponding enum member.

        Raises:
            KeyError: If `name` is not a valid member of the enum.
        """
        try:
            return cls[name]
        except KeyError:
            valid = ", ".join([e.name for e in cls])
            raise KeyError(f"Invalid PnmFileType name: {name!r}. Valid names: {valid}")
