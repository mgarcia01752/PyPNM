# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from typing import Any, Dict, List, cast
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, BaseAnalysisModel


class MultiAnalysis:
    """
    Container for managing multiple `Analysis` objects and their associated models.

    This class is designed to:
    - Store multiple `Analysis` instances.
    - Provide easy access to their models and combined data.
    - Convert collected models into Python dictionaries for JSON serialization.
    """

    def __init__(self) -> None:
        """Initialize an empty MultiAnalysis container."""
        self._analysis_list: List[Analysis] = []
        self._models: List[BaseAnalysisModel] = []
        self._dicts: List[Dict[str, Any]] = []

    def add(self, analysis: Analysis) -> None:
        """
        Add a new `Analysis` to the collection.

        Parameters
        ----------
        analysis : Analysis
            The analysis instance to be added.

        Notes
        -----
        - Extends the internal list of models and dicts with those provided by the analysis.
        """
        models = cast(List[BaseAnalysisModel], analysis.get_model())
        self._models.extend(models)

        dicts = analysis.get_dicts()
        if dicts:
            self._dicts.extend(dicts)

        self._analysis_list.append(analysis)

    def get_analyses(self) -> List[Analysis]:
        """
        Retrieve all stored analyses.

        Returns
        -------
        List[Analysis]
            A list of Analysis objects in the order they were added.
        """
        return self._analysis_list

    def length(self) -> int:
        """
        Get the total number of stored analyses.

        Returns
        -------
        int
            The count of stored Analysis objects.
        """
        return len(self._analysis_list)

    def to_model(self) -> List[BaseAnalysisModel]:
        """
        Get a flattened list of all models from all analyses.

        Returns
        -------
        List[BaseAnalysisModel]
            A list of all models collected from the added analyses.
        """
        return self._models

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert all collected analysis data into a structured dictionary.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing all collected analysis dictionaries.

        Example
        -------
        >>> multi_analysis.to_dict()
        {
            "analyses": [
                {"channel_id": 1, "metrics": {...}},
                {"channel_id": 2, "metrics": {...}}
            ]
        }
        """
        return {
            "analyses": self._dicts if self._dicts else []
        }
