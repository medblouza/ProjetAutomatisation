from __future__ import annotations

import json
import re
from typing import Any, Optional


# ============================================================
# EXCEPTION
# ============================================================

class LLMJsonError(Exception):
    """
    Raised when an LLM response cannot be turned into valid JSON.
    """
    pass


# ============================================================
# MARKDOWN FENCES
# ============================================================

def _strip_markdown_fences(
    text: str,
) -> str:

    text = text.strip()

    fence_match = re.match(
        r"^```(?:json)?\s*(.*?)\s*```$",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if fence_match:

        return fence_match.group(1).strip()

    return text


# ============================================================
# EXTRACT JSON OBJECT ONLY
# ============================================================

def _extract_first_json_object(
    text: str,
) -> Optional[str]:

    """
    Find a complete top-level JSON OBJECT.

    IMPORTANT:

    This function intentionally searches ONLY for {...}.

    It does NOT search for [...].

    This prevents a situation where Gemini returns an incomplete
    root object containing an internal array and the parser
    incorrectly returns that internal array as the root result.
    """

    start = text.find("{")

    if start == -1:

        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(
        start,
        len(text),
    ):

        char = text[i]

        # ----------------------------------------------------
        # Handle JSON strings
        # ----------------------------------------------------

        if in_string:

            if escape:

                escape = False

            elif char == "\\":

                escape = True

            elif char == '"':

                in_string = False

            continue

        # ----------------------------------------------------
        # Start / end string
        # ----------------------------------------------------

        if char == '"':

            in_string = True

            continue

        # ----------------------------------------------------
        # Object depth
        # ----------------------------------------------------

        if char == "{":

            depth += 1

        elif char == "}":

            depth -= 1

            if depth == 0:

                return text[
                    start : i + 1
                ]

    # --------------------------------------------------------
    # No complete object found.
    #
    # This usually means the LLM response was truncated.
    # --------------------------------------------------------

    return None


# ============================================================
# LIGHTWEIGHT JSON REPAIR (last resort, before giving up)
# ============================================================

# Matches `: BareWord ,` or `: BareWord }` or `: BareWord ]` where BareWord
# is NOT already quoted, and is not one of the JSON literals (true/false/
# null) or a number. This is the exact shape of the observed failure:
#     "title": Instagram,
# We deliberately only touch unquoted bare-word values — never keys, never
# already-quoted strings — to keep this repair conservative.
_BARE_WORD_VALUE_RE = re.compile(
    r'(:\s*)([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ0-9_\-\s]*?)(\s*[,\}\]])'
)

_JSON_LITERALS = {"true", "false", "null"}


def _quote_bare_word_values(text: str) -> str:
    def _replace(match: "re.Match[str]") -> str:
        prefix, value, suffix = match.group(1), match.group(2), match.group(3)
        stripped = value.strip()

        if stripped.lower() in _JSON_LITERALS:
            return match.group(0)

        try:
            float(stripped)
            return match.group(0)
        except ValueError:
            pass

        return f'{prefix}"{stripped}"{suffix}'

    return _BARE_WORD_VALUE_RE.sub(_replace, text)


def _attempt_json_repair(text: str) -> str:
    """
    Applies conservative, targeted fixes for JSON syntax mistakes commonly
    made by LLMs. Only called as a last resort, after a direct parse (and,
    for objects, object-extraction) has already failed.
    """
    return _quote_bare_word_values(text)


# ============================================================
# SAFE JSON PARSE
# ============================================================

def safe_json_parse(
    raw_text: str,
    *,
    expected_root: str = "object",
) -> Any:

    """
    Parse LLM output into a Python object.

    Parameters
    ----------
    raw_text:
        Raw response returned by the LLM.

    expected_root:
        "object" -> dict required
        "array"  -> list required
        "any"    -> dict or list accepted

    IMPORTANT:
    We never silently extract an internal JSON array from an
    incomplete JSON object.

    Example of BAD behavior:

        {
            "pages": [
                {...}
            ]

    Old parser could return:

        [
            {...}
        ]

    This parser correctly raises LLMJsonError instead.
    """

    # ========================================================
    # EMPTY RESPONSE
    # ========================================================

    if not raw_text or not raw_text.strip():

        raise LLMJsonError(
            "Empty response from LLM."
        )

    # ========================================================
    # CLEAN MARKDOWN
    # ========================================================

    cleaned = _strip_markdown_fences(
        raw_text
    )

    # ========================================================
    # DIRECT JSON PARSE
    # ========================================================

    try:

        result = json.loads(
            cleaned
        )

    except json.JSONDecodeError as direct_error:

        # ----------------------------------------------------
        # If an OBJECT is expected, try to extract only a
        # complete top-level object, then try repairing it.
        # ----------------------------------------------------

        if expected_root == "object":

            extracted = _extract_first_json_object(
                cleaned
            )

            if extracted:

                try:

                    result = json.loads(
                        extracted
                    )

                except json.JSONDecodeError:

                    # Last resort: repair common LLM syntax slips
                    # (e.g. unquoted bare-word string values) and retry.
                    repaired = _attempt_json_repair(extracted)

                    try:

                        result = json.loads(repaired)

                    except json.JSONDecodeError as e:

                        raise LLMJsonError(
                            "Found a JSON object-like block "
                            "but it could not be parsed, even after "
                            "attempting a repair. "
                            f"JSON error: {e}"
                        ) from e

            else:

                raise LLMJsonError(
                    "No complete JSON object found. "
                    "The LLM response may be truncated. "
                    f"JSON error: {direct_error}"
                ) from direct_error

        # ----------------------------------------------------
        # ARRAY EXPECTED
        # ----------------------------------------------------

        elif expected_root == "array":

            # Last resort: repair common LLM syntax slips
            # (e.g. unquoted bare-word string values) and retry.
            repaired = _attempt_json_repair(cleaned)

            try:

                result = json.loads(
                    repaired
                )

            except json.JSONDecodeError as e:

                raise LLMJsonError(
                    "Expected a JSON array but the response "
                    "could not be parsed, even after attempting a repair. "
                    f"JSON error: {e}"
                ) from e

        # ----------------------------------------------------
        # ANY ROOT
        # ----------------------------------------------------

        elif expected_root == "any":

            repaired = _attempt_json_repair(cleaned)

            try:

                result = json.loads(repaired)

            except json.JSONDecodeError as e:

                raise LLMJsonError(
                    "Invalid JSON response, even after attempting a repair. "
                    f"JSON error: {e}"
                ) from e

        else:

            raise ValueError(
                "expected_root must be "
                "'object', 'array' or 'any'."
            )

    # ========================================================
    # ROOT TYPE VALIDATION
    # ========================================================

    if expected_root == "object":

        if not isinstance(
            result,
            dict,
        ):

            raise LLMJsonError(
                "JSON is valid, but the root element is "
                f"{type(result).__name__}. "
                "Expected a JSON object."
            )

    elif expected_root == "array":

        if not isinstance(
            result,
            list,
        ):

            raise LLMJsonError(
                "JSON is valid, but the root element is "
                f"{type(result).__name__}. "
                "Expected a JSON array."
            )

    elif expected_root == "any":

        if not isinstance(
            result,
            (dict, list),
        ):

            raise LLMJsonError(
                "JSON root must be an object or an array."
            )

    else:

        raise ValueError(
            "expected_root must be "
            "'object', 'array' or 'any'."
        )

    # ========================================================
    # SUCCESS
    # ========================================================

    return result