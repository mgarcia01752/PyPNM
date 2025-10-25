
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import MutableMapping, Set, TypeVar
from typing import Any, Iterable

T = TypeVar("T")

class DictUtils:
    @staticmethod
    def rename_key(d: MutableMapping[str, Any], old: str, new: str) -> bool:
        """
        Rename key `old` -> `new` in-place. Returns True if renamed, else False.
        """
        if old == new:
            return old in d
        try:
            d[new] = d.pop(old)
            return True
        except KeyError:
            return False

    @staticmethod
    def pop_key(d: MutableMapping[str, Any], key: str) -> bool:
        """
        Pop `key` from dict in-place. Returns True if key existed and was removed.
        """
        return d.pop(key, None) is not None


class NestedDictCleaner:
    @staticmethod
    def pop_keys_recursive(
        obj: Any,
        keys_to_remove: Iterable[str],
        *,
        case_sensitive: bool = True,
        in_place: bool = True,
    ) -> Any:
        """
        Recursively remove keys from nested dict/list/tuple/set structures.

        Args:
            obj: Arbitrary nested structure (dict/list/tuple/set/scalars).
            keys_to_remove: Iterable of key strings to remove from any dict encountered.
            case_sensitive: If False, key comparison is done case-insensitively.
            in_place: If True, mutate dicts/lists in-place where possible.
                      If False, return a cleaned deep structure without touching `obj`.

        Returns:
            The cleaned structure (same object when `in_place=True` where possible).
        """
        targets: Set[str] = set(keys_to_remove)
        targets_lower: Set[str] | None = None
        if not case_sensitive:
            targets_lower = {k.lower() for k in targets}

        def _matches(key: str) -> bool:
            if case_sensitive:
                return key in targets
            # mypy: targets_lower cannot be None here
            return key.lower() in targets_lower  # type: ignore[arg-type]

        def _walk(node: Any) -> Any:
            # Dict-like
            if isinstance(node, dict):
                d = node if in_place else dict(node)

                # compute keys to delete (fixed ternary from your error)
                if case_sensitive:
                    to_delete = [k for k in list(d.keys()) if k in targets]
                else:
                    # safe because we precomputed targets_lower
                    to_delete = [k for k in list(d.keys()) if k.lower() in targets_lower]  # type: ignore[arg-type]

                for k in to_delete:
                    d.pop(k, None)

                # recurse values
                for k, v in list(d.items()):
                    d[k] = _walk(v)
                return d

            # Lists
            if isinstance(node, list):
                if in_place:
                    for i, v in enumerate(node):
                        node[i] = _walk(v)
                    return node
                return [_walk(v) for v in node]

            # Tuples
            if isinstance(node, tuple):
                return tuple(_walk(v) for v in node)

            # Sets (note: non-hashable nested results will raise; typical use keeps scalars)
            if isinstance(node, set):
                return { _walk(v) for v in node }

            # Scalars
            return node

        return _walk(obj)
