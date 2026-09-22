"""Deterministic Pydantic materialization used by offline Strands fixture models."""
from __future__ import annotations

import types
from enum import Enum
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel


def _value(annotation: Any):
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Literal:
        return args[0] if args else None
    if origin in (list, set, frozenset):
        return [] if origin is list else origin()
    if origin is tuple:
        return ()
    if origin is dict:
        return {}
    if origin in (Union, types.UnionType):
        concrete = [arg for arg in args if arg is not type(None)]
        return None if len(concrete) != len(args) else _value(concrete[0])
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return deterministic_instance(annotation)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return next(iter(annotation)).value
    if annotation is str:
        return ""
    if annotation is bool:
        return False
    if annotation is int:
        return 0
    if annotation is float:
        return 0.0
    if annotation is bytes:
        return b""
    return None


def deterministic_instance(model: type[BaseModel]) -> BaseModel:
    values = {}
    for name, field in model.model_fields.items():
        if not field.is_required():
            continue
        values[name] = _value(field.annotation)
    return model.model_validate(values)
