# tests/test_dictutils_unified.py
from __future__ import annotations

from typing import Optional
import pytest
from pydantic import BaseModel

from pypnm.lib.dict_utils import DictUtils


class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None


def test_rename_and_pop_key() -> None:
    d = {"old": 1, "keep": 2}
    assert DictUtils.rename_key(d, "old", "new") is True
    assert d == {"new": 1, "keep": 2}
    assert DictUtils.pop_key(d, "keep") is True
    assert d == {"new": 1}
    assert DictUtils.pop_key(d, "missing") is False


def test_pop_keys_recursive_copy_and_case() -> None:
    data = {
        "A": 1,
        "b": {"A": 2, "keep": 3},
        "list": [{"a": 4}, {"A": 5}],
        "tuple": ({"a": 6}, 7),
    }
    cleaned = DictUtils.pop_keys_recursive(data, ["a"], case_sensitive=False, in_place=False)
    assert cleaned == {"b": {"keep": 3}, "list": [{}, {}], "tuple": ({}, 7)}
    # original unchanged
    assert "A" in data and "b" in data


def test_models_to_nested_dict_list_and_keyed() -> None:
    users = [User(id=1, name="Ada"), User(id=2, name="Linus")]
    # list shape (exclude_none default True removes email)
    payload = DictUtils.models_to_nested_dict(users, "users")
    assert payload == {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Linus"}]}

    # keyed by id
    keyed = DictUtils.models_to_nested_dict(users, "users", by="id")
    assert keyed == {
        "users": {
            1: {"id": 1, "name": "Ada"},
            2: {"id": 2, "name": "Linus"},
        }
    }

    # include None if desired
    with_none = DictUtils.models_to_nested_dict(users, "users", exclude_none=False)
    assert with_none == {
        "users": [{"id": 1, "name": "Ada", "email": None}, {"id": 2, "name": "Linus", "email": None}]
    }


def test_models_to_nested_dict_errors() -> None:
    users = [User(id=1, name="Ada"), User(id=1, name="Dup")]
    with pytest.raises(ValueError, match="Duplicate key"):
        DictUtils.models_to_nested_dict(users, "users", by="id")

    # Missing `by` key/attr
    raw = [{"id": 1, "name": "Ada"}]
    with pytest.raises(ValueError, match="does not provide 'missing'"):
        DictUtils.models_to_nested_dict(raw, "users", by="missing")
