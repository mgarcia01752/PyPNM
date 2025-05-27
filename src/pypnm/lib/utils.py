# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import time
from enum import Enum

class TimeUnit(Enum):
    SECONDS = 's'
    MILLISECONDS = 'ms'
    NANOSECONDS = 'ns'

class Utils:

    @staticmethod
    def time_stamp(unit: TimeUnit = TimeUnit.SECONDS) -> int:
        """
        Returns the current timestamp in the specified unit.

        Args:
            unit (TimeUnit): The unit for the timestamp. Defaults to TimeUnit.SECONDS.

        Returns:
            int: The current time in the chosen unit since the epoch.
        """
        if unit == TimeUnit.NANOSECONDS:
            return time.time_ns()
        elif unit == TimeUnit.MILLISECONDS:
            return time.time_ns() // 1_000_000
        return int(time.time())
