"""
app/agents/site_structure_agent.py

Role : transformer les pages extraites du CDC en structure de routes
pour le site genere.

Contraintes :
- 1 page = 1 route.
- Respecter strictement le CDC : aucune page inventee, aucune page omise.
- Logique deterministe, aucun appel LLM.
"""
import logging
import re

from app.mcp.agents.sitegen.schemas import CDCData, Route, SiteStructure

logger = logging.getLogger(__name__)

# Noms de page consideres comme la page d'accueil (insensible a la casse).
HOME_PAGE_NAMES = {"home", "accueil", "index", "homepage", "accueil principal"}


def _slugify(name: str) -> str:
    """Convertit un nom de page en slug url-safe (ex: 'A Propos' -> 'a-propos')."""
    slug = (name or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "page"


def generate_site_structure(cdc: CDCData) -> SiteStructure:
    """
    Construit la SiteStructure (liste de routes) a partir de cdc.pages.

    - La page nommee "home"/"accueil"/... devient la route "/".
    - Chaque autre page devient une route "/<slug>".
    - Les pages sans nom sont ignorees (donnee invalide du CDC).
    """
    routes = []

    for page in cdc.pages:
        page_name = (page.name or "").strip()
        if not page_name:
            logger.warning("[SiteStructure] Page sans nom ignoree")
            continue

        if page_name.lower() in HOME_PAGE_NAMES:
            page_key = "home"
            url = "/"
        else:
            page_key = _slugify(page_name)
            url = f"/{page_key}"

        routes.append(Route(page=page_key, url=url, sections=page.sections))

    structure = SiteStructure(routes=routes)
    logger.info("[SiteStructure] %d route(s) generee(s)", len(routes))
    return structure
