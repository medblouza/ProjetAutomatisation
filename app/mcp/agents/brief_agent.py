"""
Génère un résumé créatif du site : positionnement, paragraphes marketing,
angle rédactionnel et idées visuelles.
"""
import logging
from app.llm.llm_tool import LLMTool
from app.utils.parsers import safe_parse_json, safe_string, safe_list

logger = logging.getLogger(__name__)


class BriefAgent:
    """
    Input  : dict (output de AnalyzerAgent)
    Output : dict enrichi avec la clé "brief" contenant le résumé créatif
    """

    def __init__(self, llm: LLMTool):
        self.llm = llm

    def run(self, analyzed_data: dict) -> dict:
        logger.info("[BriefAgent] Génération du brief créatif...")

        prompt  = self._build_prompt(analyzed_data)
        response = self.llm.generate(prompt, expect_json=True)
        result   = safe_parse_json(response)

        if not isinstance(result, dict):
            logger.warning("[BriefAgent] LLM JSON invalide — fallback")
            result = self._manual_fallback(analyzed_data)

        # Forcer les types
        brief = {
            "resume_site":     safe_string(result.get("resume_site")),
            "idee_generale":   safe_string(result.get("idee_generale")),
            "paragraphes":     safe_list(result.get("paragraphes")),
            "angle_redac":     safe_string(result.get("angle_redac")),
            "idees_visuelles": safe_list(result.get("idees_visuelles")),
        }

        logger.info(f"[BriefAgent] ✅ Brief généré — "
                    f"{len(brief['paragraphes'])} paragraphes, "
                    f"{len(brief['idees_visuelles'])} idées visuelles")

        return {
            **analyzed_data,
            "brief": brief,
        }

    def _build_prompt(self, data: dict) -> str:
        services      = safe_string(data.get("services", []))
        differentials = safe_string(data.get("differentiators", []))
        keywords      = safe_string(data.get("keywords", []))
        branding      = data.get("branding", {})
        colors        = ", ".join(str(c) for c in branding.get("colors", []) if c)
        styles        = ", ".join(
            s.get("name", "") if isinstance(s, dict) else str(s)
            for s in branding.get("style", [])
        )

        return f"""Tu es un chef de projet web spécialisé en rédaction, UX, branding et direction artistique.
À partir du brief suivant, produis un résumé créatif complet.

BRIEF CLIENT :
- Entreprise : {data.get('company_name', '')}
- Activité : {data.get('activity', '')}
- Ville : {data.get('city', '')}
- Cible : {data.get('target', '')}
- Services : {services}
- Points différenciants : {differentials}
- Expérience : {data.get('experience', '')}
- Zone : {data.get('zone', '')}
- Mots-clés : {keywords}
- Couleurs : {colors}
- Style : {styles}

Tu dois répondre UNIQUEMENT en JSON valide avec cette structure exacte :
{{
  "resume_site": "Résumé du site en 2-3 phrases, clair et percutant",
  "idee_generale": "Idée générale du positionnement en 1 phrase forte",
  "paragraphes": [
    "Paragraphe marketing 1 (60-80 mots)",
    "Paragraphe marketing 2 (60-80 mots)",
    "Paragraphe marketing 3 (60-80 mots)",
    "Paragraphe marketing 4 (60-80 mots)",
    "Paragraphe marketing 5 (60-80 mots)"
  ],
  "angle_redac": "Angle rédactionnel en 1-2 phrases (ton, style, approche)",
  "idees_visuelles": [
    "Idée visuelle 1 pour le graphisme",
    "Idée visuelle 2 pour le graphisme",
    "Idée visuelle 3 pour le graphisme",
    "Idée visuelle 4 pour le graphisme",
    "Idée visuelle 5 pour le graphisme"
  ]
}}"""

    def _manual_fallback(self, data: dict) -> dict:
        company  = data.get("company_name", "")
        activity = data.get("activity", "")
        city     = data.get("city", "")
        services = safe_list(data.get("services", []))

        return {
            "resume_site":     f"{company} est spécialisé en {activity} à {city}.",
            "idee_generale":   f"Expert local en {activity}",
            "paragraphes":     [
                f"{company} vous propose des services de qualité en {activity}.",
                f"Basé à {city}, nous intervenons sur toute la zone.",
                f"Notre expertise : {', '.join(services[:3]) if services else activity}",
            ],
            "angle_redac":     "Ton professionnel et accessible, centré sur la proximité locale.",
            "idees_visuelles": [
                "Photos professionnelles des réalisations",
                "Palette de couleurs cohérente avec la charte",
                "Typographie moderne et lisible",
                "Icônes minimalistes pour les services",
                "Mise en page épurée avec espaces blancs",
            ],
        }