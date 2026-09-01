"""
LenientBaseModel — base Pydantic model for any schema populated directly
from raw LLM JSON.

LLMs routinely produce technically-invalid-but-clearly-intentional values:
`null` instead of an empty string/list/dict, a number where a string was
expected, `null` inside a Dict[str, str] (e.g. a missing social link), etc.

Instead of the whole pipeline crashing with a 500/502 every time a new LLM
(or a new prompt run) produces one of these known-safe quirks in a slightly
different place, this base model coerces those specific patterns into
something schema-valid BEFORE Pydantic's own validation runs.

IMPORTANT: this is intentionally narrow. It does NOT swallow genuine
structural problems — an invalid ComponentType enum value, a missing
required object, a malformed nested shape, etc. still raise a
ValidationError as before. This only absorbs the "None instead of empty"
and "wrong primitive type" class of LLM noise, so the pipeline doesn't need
a bespoke patch every time that noise shows up in a new field.
"""

from __future__ import annotations

from typing import Any, Dict, List, Union, get_args, get_origin

from pydantic import BaseModel, model_validator


def _is_optional(tp: Any) -> bool:
    return get_origin(tp) is Union and type(None) in get_args(tp)


def _strip_optional(tp: Any) -> Any:
    if _is_optional(tp):
        args = [a for a in get_args(tp) if a is not type(None)]
        return args[0] if len(args) == 1 else Union[tuple(args)]  # noqa: UP007
    return tp


def _coerce_value(value: Any, annotation: Any) -> Any:
    if annotation is None:
        return value

    optional = _is_optional(annotation)
    inner = _strip_optional(annotation)
    origin = get_origin(inner)

    # ---- None handling: only fill in a safe empty default when the field
    # is NOT itself Optional (an Optional field is allowed to stay None).
    if value is None:
        if optional:
            return None
        if inner is str:
            return ""
        if origin in (list, List):
            return []
        if origin in (dict, Dict):
            return {}
        if inner is bool:
            return False
        # Numeric or unknown required fields: leave as None, let Pydantic
        # raise — we don't want to invent a fake number.
        return value

    # ---- Required str field but got a non-str primitive (int/float/bool)
    if inner is str and not isinstance(value, str):
        return str(value)

    # ---- List[...] handling: drop None items, stringify str-typed items
    if origin in (list, List) and isinstance(value, list):
        args = get_args(inner)
        item_type = args[0] if args else Any
        cleaned = []
        for item in value:
            if item is None:
                continue
            if item_type is str and not isinstance(item, str):
                item = str(item)
            cleaned.append(item)
        return cleaned

    # ---- Dict[str, X] handling: drop keys whose value is None,
    # stringify str-typed values (this is exactly the
    # footer_social_links / social_links case)
    if origin in (dict, Dict) and isinstance(value, dict):
        args = get_args(inner)
        val_type = args[1] if len(args) == 2 else Any
        cleaned = {}
        for k, v in value.items():
            if v is None:
                continue
            if val_type is str and not isinstance(v, str):
                v = str(v)
            cleaned[k] = v
        return cleaned

    return value


class LenientBaseModel(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def _coerce_llm_quirks(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        cleaned = dict(data)
        for name, field in cls.model_fields.items():
            if name not in cleaned:
                continue
            cleaned[name] = _coerce_value(cleaned[name], field.annotation)
        return cleaned