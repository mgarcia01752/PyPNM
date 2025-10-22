
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

class DictUtils:
    @staticmethod
    def rename_key(d: dict, old: str, new: str) -> bool:
        """Rename key `old` to `new` in-place. Returns True if renamed, else False."""
        if old == new:
            return old in d
        try:
            d[new] = d.pop(old)
            return True
        except KeyError:
            return False
