"""
Génère la stratégie marketing et les objectifs du site web.
"""
import logging
from app.llm.llm_tool import LLMTool
from app.utils.parsers import safe_parse_json, safe_string, safe_list

logger = logging.getLogger(__name__)


class StrategyAgent:
    """
    Input  : dict (output de AnalyzerAgent)
    Output : dict avec objectifs, messages clés, ton éditorial, CTA
    """

    def __init__(self, llm: LLMTool):
        self.llm = llm

    def run(self, analyzed_data: dict) -> dict:
        logger.info("[StrategyAgent] Génération stratégie marketing...")

        prompt   = self._build_prompt(analyzed_data)
        response = self.llm.generate(prompt, expect_json=True)
        result   = safe_parse_json(response)

        if not isinstance(result, dict):
            logger.warning("[StrategyAgent] LLM JSON invalide — fallback")
            result = self._manual_fallback(analyzed_data)

        output = {
            **analyzed_data,
            "strategy": {
                "objectives":    safe_list(result.get("objectives")),
                "key_messages":  safe_list(result.get("key_messages")),
                "tone":          safe_string(result.get("tone")),
                "cta_primary":   safe_string(result.get("cta_primary")),
                "cta_secondary": safe_string(result.get("cta_secondary")),
                "seo_angle":     safe_string(result.get("seo_angle")),
                "unique_value":  safe_string(result.get("unique_value")),
            }
        }

        logger.info(f"[StrategyAgent] ✅ Stratégie générée — "
                    f"{len(output['strategy']['objectives'])} objectifs, "
                    f"{len(output['strategy']['key_messages'])} messages clés")
        return output

    def _build_prompt(self, data: dict) -> str:
        services  = safe_string(data.get("services", []))
        diff      = safe_string(data.get("differentiators", []))
        keywords  = safe_string(data.get("keywords", []))

        return f"""Tu es un expert en stratégie marketing digital pour PME françaises.
À partir des données suivantes, génère une stratégie marketing pour le site web.

ENTREPRISE :
- Nom : {data.get('company_name', '')}
- Activité : {data.get('activity', '')}
- Ville : {data.get('city', '')}
- Cible : {data.get('target', '')}
- Services : {services}
- Points différenciants : {diff}
- Mots-clés : {keywords}
- Zone : {data.get('zone', '')}

Retourne UNIQUEMENT ce JSON valide :
{{
  "objectives": [
    "Objectif 1 du site web",
    "Objectif 2 du site web",
    "Objectif 3 du site web"
  ],
  "key_messages": [
    "Message clé 1 à communiquer",
    "Message clé 2 à communiquer",
    "Message clé 3 à communiquer"
  ],
  "tone": "description du ton éditorial (ex: professionnel et chaleureux)",
  "cta_primary": "texte du bouton d'action principal (ex: Demander un devis)",
  "cta_secondary": "texte du bouton secondaire (ex: Découvrir nos services)",
  "seo_angle": "angle SEO principal en 1 phrase",
  "unique_value": "proposition de valeur unique en 1-2 phrases"
}}"""

    def _manual_fallback(self, data: dict) -> dict:
        company  = data.get("company_name", "")
        activity = data.get("activity", "")
        city     = data.get("city", "")
        return {
            "objectives":    [
                f"Présenter {company} et ses services",
                "Générer des demandes de devis",
                f"Être visible localement à {city}",
            ],
            "key_messages":  [
                f"Expert en {activity} à {city}",
                safe_string(data.get("differentiators", [])),
            ],
            "tone":          "Professionnel et accessible",
            "cta_primary":   "Demander un devis",
            "cta_secondary": "Découvrir nos services",
            "seo_angle":     f"{activity} à {city}",
            "unique_value":  safe_string(data.get("strengths", "")),
        }