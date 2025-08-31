# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import List, TypeVar
from pypnm.lib.types import Number

KHZ:Number                  = 1_000
MHZ:Number                  = 1_000_000
GHZ:Number                  = 1_000_000_000

NULL_ARRAY_NUMBER:List[Number] = [0]

INVALID_CHANNEL_ID: int     = -1
INVALID_PROFILE_ID:int      = -1

T = TypeVar("T")