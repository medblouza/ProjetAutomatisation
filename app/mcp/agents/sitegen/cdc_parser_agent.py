"""
app/agents/cdc_parser_agent.py

Role : extraire un JSON structure STRICT depuis le texte brut du cahier
des charges (issu de PDF/DOCX/TXT).

Regles :
- NE PAS inventer de pages.
- NE PAS ajouter de contenu absent du texte.
- Extraction uniquement.

Appel LLM exclusivement via app/llm/llm_tool.py (LLMTool).
"""
import json
import logging

from app.mcp.agents.sitegen.schemas import CDCData
from app.llm.llm_tool import LLMTool

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """Tu es un extracteur de donnees structurees a partir d'un cahier des charges.

REGLES STRICTES :
- Extraction UNIQUEMENT. N'invente AUCUNE page, section, couleur ou information absente du texte.
- Si une information n'est pas presente dans le texte, laisse la valeur vide ("" ou []).
- Ne reformule pas, n'ajoute pas de contenu marketing.
- Reponds UNIQUEMENT avec un objet JSON valide, sans bloc markdown, sans commentaire, sans texte autour.

FORMAT JSON ATTENDU (respecte exactement cette structure) :
{{
  "company": {{
    "name": "",
    "activity": "",
    "location": ""
  }},
  "branding": {{
    "colors": [],
    "style": "",
    "typography": ""
  }},
  "pages": [
    {{
      "name": "",
      "sections": [
        {{"name": "", "content": ""}}
      ]
    }}
  ],
  "features": [],
  "seo": {{}}
}}

TEXTE DU CAHIER DES CHARGES :
---
{cdc_text}
---

Reponds uniquement avec le JSON."""


# Taille max du texte injecte dans le prompt (securite contexte LLM).
MAX_INPUT_CHARS = 12000


def _empty_cdc() -> CDCData:
    """Retourne un CDCData vide (utilise en cas d'echec total)."""
    return CDCData()


def parse_cdc(cdc_text: str, llm: LLMTool) -> CDCData:
    """
    Extrait un CDCData structure et valide a partir du texte brut.

    Ne leve jamais d'exception : retourne un CDCData vide en cas d'echec
    (reponse LLM vide, JSON invalide, validation Pydantic echouee).
    """
    if not cdc_text or not cdc_text.strip():
        logger.warning("[CDCParser] Texte d'entree vide")
        return _empty_cdc()

    prompt = PROMPT_TEMPLATE.format(cdc_text=cdc_text.strip()[:MAX_INPUT_CHARS])

    raw = llm.generate(prompt, expect_json=True)

    if not raw:
        logger.error("[CDCParser] Reponse LLM vide - retour d'un CDC vide")
        return _empty_cdc()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(f"[CDCParser] JSON invalide ({exc}) - retour d'un CDC vide")
        return _empty_cdc()

    if not isinstance(data, dict):
        logger.error("[CDCParser] Le JSON retourne n'est pas un objet - retour d'un CDC vide")
        return _empty_cdc()

    try:
        cdc = CDCData(**data)
    except Exception as exc:  # validation Pydantic
        logger.error(f"[CDCParser] Validation Pydantic echouee ({exc}) - retour d'un CDC vide")
        return _empty_cdc()

    logger.info(
        "[CDCParser] OK - entreprise='%s' pages=%d features=%d",
        cdc.company.name,
        len(cdc.pages),
        len(cdc.features),
    )
    return cdc
