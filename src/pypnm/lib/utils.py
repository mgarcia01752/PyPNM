from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import time
import hashlib
from enum import Enum

from pypnm.lib.types import TimeStamp, TransactionId


class TimeUnit(Enum):
    SECONDS      = "s"
    MILLISECONDS = "ms"
    NANOSECONDS  = "ns"


class Utils:

    @staticmethod
    def time_stamp(unit: TimeUnit = TimeUnit.SECONDS) -> TimeStamp:
        """
        Return The Current Timestamp In The Specified Unit.

        Parameters
        ----------
        unit:
            Time unit used for the returned timestamp. Defaults to
            ``TimeUnit.SECONDS``.

        Returns
        -------
        int
            Current time since the Unix epoch expressed in the requested
            unit.
        """
        if unit == TimeUnit.NANOSECONDS:
            return time.time_ns()
        if unit == TimeUnit.MILLISECONDS:
            return time.time_ns() // 1_000_000
        return int(time.time())

    @staticmethod
    def generate_transaction_id(seed: int | None = None, length: int = 24) -> TransactionId:
        """
        Generate A Hashed Time-Based Transaction Identifier.

        The identifier is derived from the current time in nanoseconds using
        ``Utils.time_stamp(unit=TimeUnit.NANOSECONDS)`` and then hashed with
        SHA-256. When ``seed`` is provided, it is concatenated with the
        timestamp as ``"<timestamp_ns>:<seed>"`` before hashing, allowing
        deterministic diversification of IDs for a given timestamp source.

        The resulting hex digest is truncated to ``length`` characters. The
        effective length is clamped to the range ``[1, len(digest)]`` so that
        values less than or equal to zero or greater than the digest length
        fall back to the full digest length.

        Parameters
        ----------
        seed:
            Optional integer seed that is combined with the nanosecond
            timestamp prior to hashing. When omitted, only the timestamp
            is hashed.
        length:
            Desired length of the returned hexadecimal transaction identifier.
            Defaults to ``24`` characters.

        Returns
        -------
        TransactionId
            Hash-based transaction identifier with the requested (clamped)
            length.
        """
        base_value: int = Utils.time_stamp(unit=TimeUnit.NANOSECONDS)
        if seed is not None:
            raw_value: str = f"{base_value}:{seed}"
        else:
            raw_value: str = str(base_value)

        digest_full: str = hashlib.sha256(raw_value.encode("utf-8")).hexdigest()
        max_length: int  = len(digest_full)

        effective_length: int = length
        if effective_length <= 0 or effective_length > max_length:
            effective_length = max_length

        truncated: str = digest_full[:effective_length]
        return TransactionId(truncated)
