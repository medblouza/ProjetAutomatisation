"""
Contrôle qualité du CDC : score, corrections, amélioration.
"""
import logging
from app.llm.llm_tool import LLMTool
from app.utils.parsers import safe_parse_json, safe_string, safe_int

logger = logging.getLogger(__name__)

# Champs obligatoires pour le score
REQUIRED_FIELDS = [
    "company_name", "activity", "city", "target",
    "services", "differentiators", "strategy",
    "site_structure", "cdc_content",
]


class QAAgent:
    """
    Input  : dict (output de ContentAgent)
    Output : dict { "score": int, "content": string, "issues": list }
    """

    def __init__(self, llm: LLMTool):
        self.llm = llm

    def run(self, content_data: dict) -> dict:
        logger.info("[QAAgent] Contrôle qualité du CDC...")

        # Score structurel (sans LLM)
        structural_score, issues = self._structural_check(content_data)
        logger.info(f"[QAAgent] Score structurel : {structural_score}/100 — {len(issues)} problème(s)")

        cdc_content = safe_string(content_data.get("cdc_content", ""))

        # Amélioration LLM si le contenu est trop court
        if len(cdc_content) < 500:
            logger.warning("[QAAgent] CDC trop court — tentative d'enrichissement")
            cdc_content = self._enrich_content(content_data, cdc_content)

        # Score LLM (évaluation qualité du contenu)
        llm_score = self._llm_quality_score(cdc_content, content_data)
        logger.info(f"[QAAgent] Score LLM : {llm_score}/100")

        # Score final pondéré
        final_score = int(structural_score * 0.4 + llm_score * 0.6)

        # Ajouter un résumé exécutif en tête du CDC
        final_content = self._add_summary(cdc_content, content_data, final_score)

        logger.info(f"[QAAgent] ✅ Score final : {final_score}/100")

        return {
            "score":   final_score,
            "content": final_content,
            "issues":  issues,
            "meta": {
                "company":        content_data.get("company_name", ""),
                "pages_count":    content_data.get("site_structure", {}).get("total_pages", 0),
                "content_length": len(final_content),
            }
        }

    # ── Vérification structurelle ─────────────────────────────────────────────
    def _structural_check(self, data: dict) -> tuple:
        issues = []
        score  = 100

        for field in REQUIRED_FIELDS:
            val = data.get(field)
            if not val:
                issues.append(f"Champ manquant : {field}")
                score -= 10

        # Vérifier les services
        services = data.get("services", [])
        if isinstance(services, list) and len(services) < 2:
            issues.append("Peu de services renseignés (< 2)")
            score -= 5

        # Vérifier les pages
        pages = data.get("site_structure", {}).get("pages", [])
        if len(pages) < 3:
            issues.append(f"Peu de pages générées ({len(pages)} < 3)")
            score -= 10

        # Vérifier le contenu CDC
        cdc = safe_string(data.get("cdc_content", ""))
        if len(cdc) < 1000:
            issues.append(f"CDC trop court ({len(cdc)} caractères)")
            score -= 15

        return max(score, 0), issues

    # ── Score LLM ────────────────────────────────────────────────────────────
    def _llm_quality_score(self, content: str, data: dict) -> int:
        if not content or len(content) < 200:
            return 30

        prompt = f"""Tu es un expert en création de sites web. Évalue ce cahier des charges sur 100.

ENTREPRISE : {data.get('company_name', '')} — {data.get('activity', '')}

CDC (extrait) :
{content[:1500]}

Évalue selon ces critères :
- Complétude des informations (25 pts)
- Qualité du contenu et pertinence (25 pts)
- Structure et lisibilité (25 pts)
- Utilité pour un développeur web (25 pts)

Retourne UNIQUEMENT un JSON : {{"score": <entier entre 0 et 100>, "comment": "<phrase courte>"}}"""

        response = self.llm.generate(prompt, expect_json=True)
        result   = safe_parse_json(response)

        if isinstance(result, dict):
            return safe_int(result.get("score"), fallback=70)

        return 70  # Score par défaut si LLM échoue

    # ── Enrichissement ────────────────────────────────────────────────────────
    def _enrich_content(self, data: dict, current_content: str) -> str:
        prompt = f"""Complète ce cahier des charges incomplet pour {data.get('company_name', '')} ({data.get('activity', '')} à {data.get('city', '')}).

CONTENU ACTUEL :
{current_content}

Ajoute les sections manquantes : présentation client, objectifs, pages, recommandations design et SEO.
Retourne le CDC complet en texte structuré avec des titres ## clairs."""

        enriched = self.llm.generate(prompt, expect_json=False)
        return enriched if enriched and len(enriched) > len(current_content) else current_content

    # ── Résumé exécutif ───────────────────────────────────────────────────────
    def _add_summary(self, content: str, data: dict, score: int) -> str:
        pages = data.get("site_structure", {}).get("pages", [])
        nav   = " | ".join(p["name"] for p in pages)

        score_label = (
            "🟢 Excellent" if score >= 80
            else "🟡 Bon" if score >= 60
            else "🟠 À améliorer" if score >= 40
            else "🔴 Insuffisant"
        )

        summary = f"""---
### 📋 RÉSUMÉ EXÉCUTIF
**Score qualité :** {score}/100 — {score_label}
**Entreprise :** {data.get('company_name', '')}
**Secteur :** {data.get('activity', '')} | **Ville :** {data.get('city', '')}
**Pages générées :** {len(pages)} ({nav})
**Longueur CDC :** {len(content)} caractères
---

"""
        return summary + content