import json
import logging
import re
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


def safe_parse_json(text: str, fallback: Any = None) -> Any:
    """
    Parse du JSON depuis une réponse LLM de façon sécurisée.
    Tente plusieurs stratégies de nettoyage avant d'abandonner.
    N'utilise jamais eval().
    """
    if not text or not isinstance(text, str):
        return fallback

    # Stratégie 1 : parse direct
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Stratégie 2 : nettoyer les balises markdown
    cleaned = re.sub(r"```json\s*", "", text)
    cleaned = re.sub(r"```\s*", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Stratégie 3 : extraire le premier objet JSON {}
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Stratégie 4 : extraire le premier tableau JSON []
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.warning(f"[Parser] safe_parse_json failed. Raw text (100 chars): {text[:100]!r}")
    return fallback


def safe_string(value: Any, fallback: str = "") -> str:
    """Force une valeur en string propre."""
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def safe_list(value: Any, fallback: Optional[List] = None) -> List:
    """Force une valeur en liste propre."""
    if fallback is None:
        fallback = []
    if value is None:
        return fallback
    if isinstance(value, list):
        return [v for v in value if v is not None]
    if isinstance(value, str):
        # Essayer de parser comme JSON
        parsed = safe_parse_json(value)
        if isinstance(parsed, list):
            return parsed
        # Sinon split par virgule/retour ligne
        items = re.split(r"[,\n]", value)
        return [i.strip() for i in items if i.strip()]
    return fallback


def safe_int(value: Any, fallback: int = 0) -> int:
    """Force une valeur en entier."""
    if value is None:
        return fallback
    try:
        return int(value)
    except (ValueError, TypeError):
        # Extraire les chiffres si du texte parasite
        match = re.search(r"\d+", str(value))
        if match:
            return int(match.group())
        return fallback


def format_list_as_text(items: List[str], prefix: str = "- ") -> str:
    """Convertit une liste en texte formaté."""
    return "\n".join(f"{prefix}{item}" for item in items if item)

