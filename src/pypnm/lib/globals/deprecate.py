
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import warnings
from functools import wraps

def deprecated(reason: str, *, since: str = "", remove_in: str = ""):
    """
    Decorator to mark functions/methods as deprecated.

    Parameters
    ----------
    reason : str
        What to use instead / why deprecated.
    since : str
        Version when deprecation started (e.g., "1.4").
    remove_in : str
        Planned removal version (e.g., "2.0").
    """
    msg_parts = []
    if since:
        msg_parts.append(f"since {since}")
    if remove_in:
        msg_parts.append(f"and will be removed in {remove_in}")
    when = (" " + " ".join(msg_parts)) if msg_parts else ""
    full_msg = f"This function is deprecated{when}. {reason}"

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # stacklevel=2 points the warning at the caller
            warnings.warn(full_msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator
