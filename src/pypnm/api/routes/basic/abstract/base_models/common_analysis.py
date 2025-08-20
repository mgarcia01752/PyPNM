# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

from pypnm.lib.types import ComplexArray


class CommonAnalysis(BaseModel):
    """
    Common analysis model for handling analysis data.

    This model is designed to be extended by specific analysis types.
    It provides a base structure for common fields and methods.
    
    Attributes:
        model_config (ConfigDict): Configuration for the Pydantic model.
    
    Flattened fields:
      - channel_id: Channel ID
      - raw_x: List of raw x-values (e.g., frequencies)
      - raw_y: List of raw y-values (e.g., magnitudes)
      - raw_complex: List of raw complex values (e.g., (real, imaginary) pairs)

    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    channel_id: int = Field(..., description="Channel ID")
    raw_x: List[Union[int , float]] = Field(..., description="Typically Frequency or index")
    raw_y: List[Union[int , float]] = Field(..., description="Typically Magnitude (dB/sec)")
    raw_complex: List[Tuple[float, float]] = Field(default=[], description="Optional complex series aligned to raw_x/raw_y")