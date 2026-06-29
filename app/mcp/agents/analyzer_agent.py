import logging
from app.llm.llm_tool import LLMTool
from app.utils.parsers import safe_parse_json, safe_string, safe_list

logger = logging.getLogger(__name__)


class AnalyzerAgent:
    """
    Input  : dict (données nettoyées du CRM)
    Output : dict avec activité, cible, services, points différenciants
    """

    def __init__(self, llm: LLMTool):
        self.llm = llm

    def run(self, raw_data: dict) -> dict:
        logger.info("[AnalyzerAgent] Démarrage analyse...")

        prompt = self._build_prompt(raw_data)
        response = self.llm.generate(prompt, expect_json=True)

        result = safe_parse_json(response)

        if not isinstance(result, dict):
            logger.warning("[AnalyzerAgent] LLM n'a pas retourné de JSON valide — fallback manuel")
            result = self._manual_fallback(raw_data)

        # Forcer les types
        output = {
            "company_name":       safe_string(result.get("company_name") or raw_data.get("company_name")),
            "activity":           safe_string(result.get("activity")     or raw_data.get("activity")),
            "city":               safe_string(result.get("city")         or raw_data.get("city")),
            "target":             safe_string(result.get("target")        or raw_data.get("target")),
            "services":           safe_list(result.get("services")        or raw_data.get("services")),
            "differentiators":    safe_list(result.get("differentiators")),
            "strengths":          safe_string(result.get("strengths")     or raw_data.get("strengths")),
            "experience":         safe_string(result.get("experience")    or raw_data.get("experience")),
            "zone":               safe_string(result.get("zone")          or raw_data.get("zone")),
            "keywords":           safe_list(result.get("keywords")        or raw_data.get("keywords")),
            "pages":              raw_data.get("pages", []),
            "branding":           raw_data.get("branding", {}),
            "social":             raw_data.get("social", {}),
        }

        logger.info(f"[AnalyzerAgent] ✅ Analyse terminée — {len(output['services'])} services, "
                    f"{len(output['differentiators'])} différenciants")
        return output

    def _build_prompt(self, data: dict) -> str:
        services_str = safe_string(data.get("services", []))
        return f"""Tu es un expert en analyse d'entreprise. Analyse ces données client et retourne UNIQUEMENT un JSON valide.

DONNÉES CLIENT :
- Entreprise : {data.get('company_name', '')}
- Activité : {data.get('activity', '')}
- Ville : {data.get('city', '')}
- Cible : {data.get('target', '')}
- Services : {services_str}
- Points forts : {data.get('strengths', '')}
- Expérience : {data.get('experience', '')}
- Concurrent : {data.get('competitor', '')}
- Détails : {data.get('company_details', '')}

Retourne UNIQUEMENT ce JSON (sans texte avant ou après) :
{{
  "company_name": "nom exact",
  "activity": "activité principale en 3-5 mots",
  "city": "ville",
  "target": "description de la cible client",
  "services": ["service1", "service2", "service3"],
  "differentiators": ["point différenciant 1", "point différenciant 2"],
  "strengths": "points forts résumés en 2-3 phrases",
  "experience": "expérience résumée",
  "zone": "zone d'intervention",
  "keywords": ["mot-clé SEO 1", "mot-clé SEO 2", "mot-clé SEO 3"]
}}"""

    def _manual_fallback(self, data: dict) -> dict:
        """Fallback si le LLM échoue — utilise les données brutes directement."""
        return {
            "company_name":    data.get("company_name", ""),
            "activity":        data.get("activity", ""),
            "city":            data.get("city", ""),
            "target":          data.get("target", ""),
            "services":        data.get("services", []),
            "differentiators": [data.get("strengths", "")],
            "strengths":       data.get("strengths", ""),
            "experience":      data.get("experience", ""),
            "zone":            data.get("zone", ""),
            "keywords":        data.get("keywords", []),
        }