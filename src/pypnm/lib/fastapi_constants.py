
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Any, Dict, cast

from pypnm.lib.types import HttpRtnCode

FAST_API_RESPONSE: Dict[int | str, Dict[str, Any]] = {
    cast(HttpRtnCode, 200): {
        "description": "JSON analysis or a downloadable archive, depending on request.output.type",
        "content": {
            "application/json": {},
            "application/zip": {},
            "application/octet-stream": {},
        },
    },
    cast(HttpRtnCode, 400): {"description": "Bad request"},
    cast(HttpRtnCode, 500): {"description": "Server error"},
}

