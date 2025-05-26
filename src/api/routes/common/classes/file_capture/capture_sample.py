# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Optional
from pydantic import BaseModel, Field

class CaptureSample(BaseModel):
    """
    Represents a single RxMER capture iteration and its associated metadata.

    Attributes:
        timestamp (float):
            Unix epoch time when the capture was initiated.
        transaction_id (str):
            Unique TFTP transaction identifier provided by the cable modem.
        filename (str):
            Name of the file uploaded via TFTP containing the capture data.
        error (Optional[str]):
            Error message explaining why the capture or upload failed, if applicable.

    Example:
        ```python
        sample = CaptureSample(
            timestamp=1684500000.0,
            transaction_id="txn12345",
            filename="rxmer_txn12345.json",
            error=None
        )
        ```
    """
    timestamp: float = Field(
        ..., 
        description="Unix timestamp (seconds since epoch) when the capture was triggered"
    )
    transaction_id: str = Field(
        ..., 
        description="TFTP transaction ID returned by the cable modem"
    )
    filename: str = Field(
        ..., 
        description="Name of the uploaded capture file containing RxMER data"
    )
    error: Optional[str] = Field(
        None, 
        description="Error message if capture or upload failed (otherwise None)"
    )
