"""
Génère l'arborescence du site web sous forme de JSON structuré.
"""
import logging
from app.llm.llm_tool import LLMTool
from app.utils.parsers import safe_parse_json, safe_string, safe_list

logger = logging.getLogger(__name__)


class StructureAgent:
    """
    Input  : dict (output de StrategyAgent)
    Output : dict avec la structure complète du site (pages + sections)
    """

    def __init__(self, llm: LLMTool):
        self.llm = llm

    def run(self, strategy_data: dict) -> dict:
        logger.info("[StructureAgent] Génération arborescence site...")

        # Utiliser les pages existantes du CRM si disponibles
        existing_pages = strategy_data.get("pages", [])

        prompt   = self._build_prompt(strategy_data, existing_pages)
        response = self.llm.generate(prompt, expect_json=True)
        result   = safe_parse_json(response)

        if not isinstance(result, dict) or "pages" not in result:
            logger.warning("[StructureAgent] LLM JSON invalide — fallback")
            result = self._manual_fallback(strategy_data, existing_pages)

        # Valider et nettoyer les pages
        clean_pages = self._clean_pages(result.get("pages", []))

        output = {
            **strategy_data,
            "site_structure": {
                "pages":       clean_pages,
                "total_pages": len(clean_pages),
                "nav_order":   [p["name"] for p in clean_pages],
            }
        }

        logger.info(f"[StructureAgent] ✅ Structure générée — {len(clean_pages)} pages")
        return output

    def _build_prompt(self, data: dict, existing_pages: list) -> str:
        strategy  = data.get("strategy", {})
        services  = safe_string(data.get("services", []))
        pages_str = ""
        if existing_pages:
            pages_str = "\nPAGES EXISTANTES DANS LE CRM :\n" + "\n".join(
                f"- {p.get('name', '')}: {p.get('content', '')[:100]}"
                for p in existing_pages
            )

        return f"""Tu es un expert UX/UI et architecte de sites web pour PME françaises.
Génère l'arborescence complète d'un site web professionnel.

ENTREPRISE :
- Nom : {data.get('company_name', '')}
- Activité : {data.get('activity', '')}
- Services : {services}
- CTA principal : {strategy.get('cta_primary', 'Demander un devis')}
- Ton : {strategy.get('tone', '')}
{pages_str}

Retourne UNIQUEMENT ce JSON valide :
{{
  "pages": [
    {{
      "name": "Accueil",
      "slug": "accueil",
      "priority": 1,
      "sections": [
        "Hero avec H1 et CTA principal",
        "Présentation rapide de l'entreprise",
        "Services en avant",
        "Points forts / différenciants",
        "Appel à l'action"
      ],
      "seo_title": "titre SEO de la page",
      "meta_description": "meta description 160 caractères"
    }},
    {{
      "name": "Nos Services",
      "slug": "services",
      "priority": 2,
      "sections": ["Liste des services", "Détail de chaque service", "CTA devis"],
      "seo_title": "titre SEO",
      "meta_description": "meta description"
    }},
    {{
      "name": "À propos",
      "slug": "a-propos",
      "priority": 3,
      "sections": ["Histoire de l'entreprise", "Valeurs", "Équipe"],
      "seo_title": "titre SEO",
      "meta_description": "meta description"
    }},
    {{
      "name": "Contact",
      "slug": "contact",
      "priority": 4,
      "sections": ["Formulaire de contact", "Coordonnées", "Carte"],
      "seo_title": "titre SEO",
      "meta_description": "meta description"
    }}
  ]
}}

Adapte les pages aux services de l'entreprise. Ajoute des pages spécifiques si pertinent."""

    def _clean_pages(self, pages: list) -> list:
        """Valide et nettoie chaque page."""
        cleaned = []
        for i, page in enumerate(pages):
            if not isinstance(page, dict):
                continue
            cleaned.append({
                "name":             safe_string(page.get("name"), f"Page {i+1}"),
                "slug":             safe_string(page.get("slug"), f"page-{i+1}"),
                "priority":         int(page.get("priority", i + 1)),
                "sections":         safe_list(page.get("sections")),
                "seo_title":        safe_string(page.get("seo_title")),
                "meta_description": safe_string(page.get("meta_description")),
            })
        return sorted(cleaned, key=lambda p: p["priority"])

    def _manual_fallback(self, data: dict, existing_pages: list) -> dict:
        """Construit une structure basique depuis les pages CRM ou par défaut."""
        company  = data.get("company_name", "")
        activity = data.get("activity", "")
        city     = data.get("city", "")
        services = safe_list(data.get("services", []))

        if existing_pages:
            pages = [
                {
                    "name":             p.get("name", ""),
                    "slug":             p.get("name", "page").lower().replace(" ", "-"),
                    "priority":         i + 1,
                    "sections":         [p.get("content", "")] if p.get("content") else [],
                    "seo_title":        f"{p.get('name', '')} — {company}",
                    "meta_description": f"{p.get('name', '')} de {company} à {city}",
                }
                for i, p in enumerate(existing_pages)
            ]
        else:
            pages = [
                {
                    "name": "Accueil", "slug": "accueil", "priority": 1,
                    "sections": ["Hero", "Services", "À propos", "CTA"],
                    "seo_title": f"{activity} à {city} — {company}",
                    "meta_description": f"{company}, expert en {activity} à {city}.",
                },
                {
                    "name": "Services", "slug": "services", "priority": 2,
                    "sections": services[:5] or ["Nos services"],
                    "seo_title": f"Services {activity} — {company}",
                    "meta_description": f"Découvrez les services de {company} à {city}.",
                },
                {
                    "name": "À propos", "slug": "a-propos", "priority": 3,
                    "sections": ["Notre histoire", "Nos valeurs"],
                    "seo_title": f"À propos — {company}",
                    "meta_description": f"En savoir plus sur {company}.",
                },
                {
                    "name": "Contact", "slug": "contact", "priority": 4,
                    "sections": ["Formulaire", "Coordonnées"],
                    "seo_title": f"Contact — {company}",
                    "meta_description": f"Contactez {company} à {city}.",
                },
            ]

        return {"pages": pages}