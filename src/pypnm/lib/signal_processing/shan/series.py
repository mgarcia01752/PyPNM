
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
from typing import Sequence, List, Dict, Any

from pydantic import BaseModel, Field

from pypnm.lib.types import FloatSeries, IntSeries, StringArray
from .shannon import Shannon

class ShannonSeriesModel(BaseModel):
    snr_db_values:FloatSeries                   = Field(...,description="")
    bits_per_symbol:IntSeries                   = Field(...,description="")
    modulations:StringArray                     = Field(...,description="")
    snr_db_limit:FloatSeries                    = Field(...,description="")
    supported_modulation_counts: Dict[str,int]  = Field(...,description="")

class ShannonSeries:
    """
    Wrapper around the Shannon estimator to process a series of SNR (dB) values.

    Attributes:
        snr_db_values    : List of input SNR values in dB.
        bits_list        : Supported bits per symbol for each SNR.
        modulations      : Recommended QAM modulation names per SNR.
    """
    def __init__(self, snr_db_values: Sequence[float]):
        """
        Initialize the series calculator.

        Parameters
        ----------
        snr_db_values : Sequence[float]
            A list of SNR values in dB. Each must be non-negative and finite.

        Raises
        ------
        ValueError
            If any SNR value is negative or non-finite.
        """
        # Validate inputs
        self.snr_db_values: List[float] = []
        for db in snr_db_values:
            if not isinstance(db, (int, float)) or db < 0 or db != db or db == float('inf'):
                raise ValueError(f"Invalid SNR dB value: {db}")
            self.snr_db_values.append(float(db))

        # Compute Shannon instances per entry
        self._instances: List[Shannon] = [Shannon(db) for db in self.snr_db_values]

        # Extract bits and modulations
        self.bits_list: List[int]       = [inst.bits for inst in self._instances]
        self.modulations: List[str]     = [inst.get_modulation() for inst in self._instances]
        self.snr_db_limit: List[float]  = self.limit()

        self._model:ShannonSeriesModel = self.__build_model()

    def __build_model(self) -> ShannonSeriesModel:

        _:ShannonSeriesModel = ShannonSeriesModel (
            bits_per_symbol             =   self.bits_list,
            modulations                 =   self.modulations,
            snr_db_values               =   self.snr_db_values,
            supported_modulation_counts = self.supported_modulation_counts(),
            snr_db_limit                = self.limit()
        )
        
        return _

    def supported_modulation_counts(self) -> Dict[str, int]:
        """
        Count how many input SNR values support each modulation up to Shannon limit.

        Returns
        -------
        Dict[str, int]
            Mapping from modulation name to count of SNR values where
            bits_per_symbol >= modulation_bits.
        """
        # Initialize counts for all known modulations
        counts: Dict[str, int] = {mod: 0 for mod in Shannon.QAM_MODULATIONS.values()}
        
        # For each sample, increment all modulations it supports
        for inst in self._instances:
            max_bits = inst.bits
            for bits, mod in Shannon.QAM_MODULATIONS.items():
                if bits <= max_bits:
                    counts[mod] += 1
        return counts

    def to_model(self) -> ShannonSeriesModel:
        return self._model

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the series results and supported counts to a dictionary.
        """
        return self.to_model().model_dump()

    def to_json(self, indent:int=2) -> str:
        """
        Serialize the series results to a JSON string.

        Returns
        -------
        str
            JSON representation of the Model.
        """
        return self.to_model().model_dump_json(indent=indent)

    def average_bits(self) -> float:
        """
        Compute the average supported bits per symbol over the series.

        Returns
        -------
        float
            Arithmetic mean of bits_list.
        """
        return sum(self.bits_list) / len(self.bits_list) if self.bits_list else 0.0

    def max_modulation(self) -> str:
        """
        Return the highest-order modulation supported in the series.

        Returns
        -------
        str
            The modulation string corresponding to the maximum bits.
        """
        if not self._instances:
            return "UNKNOWN"
        max_bits = max(self.bits_list)
        for inst in self._instances:
            if inst.bits == max_bits:
                return inst.get_modulation()
        return "UNKNOWN"

    def limit(self) -> List[float]:
        """
        Compute the Shannon limit for each SNR value in the series.

        Returns
        -------
        List[float]
            List of Shannon limits corresponding to each SNR in dB.
        """
        return Shannon.snr_to_snr_limit(self.snr_db_values)

    def __repr__(self) -> str:
        return f"ShannonSeries(snr_db_values={self.snr_db_values})"

    def __str__(self) -> str:
        return f"ShannonSeries with {len(self.snr_db_values)} SNR values: {self.snr_db_values}"