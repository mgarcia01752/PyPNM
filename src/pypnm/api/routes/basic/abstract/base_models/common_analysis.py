# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import List, Union
from pydantic import BaseModel, ConfigDict, Field


class CommonAnalysis(BaseModel):
    """
    Common analysis model for handling analysis data.

    This model is designed to be extended by specific analysis types.
    It provides a base structure for common fields and methods.
    
    Attributes:
        model_config (ConfigDict): Configuration for the Pydantic model.
    
    Flattened fields:
      - channel_id: Channel ID
      - raw_x:
      - raw_y:
    
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    channel_id: int = Field(..., description="Channel ID")
    raw_x: List[Union[int , float]] = Field(..., description="")
    raw_y: List[Union[int , float]] = Field(..., description="")
