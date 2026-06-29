"""
app/orchestrator.py

Role : orchestrer le pipeline complet de generation de site.

FLOW :
  1. recevoir le texte du CDC
  2. cdc_parser_agent       -> CDCData
  3. design_system_agent    -> DesignSystem
  4. site_structure_agent   -> SiteStructure
  5. html_generator_agent   -> fichiers HTML/CSS sur disque
  6. construire le ZIP du site genere

Retourne :
  - project_id
  - preview_html (contenu de index.html)
  - site_dir (chemin du dossier genere)
  - zip_path (chemin du ZIP genere)
  - structure (dict)
  - cdc (dict)
  - design (dict)
"""
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from app.mcp.agents.sitegen import cdc_parser_agent, design_system_agent, html_generator, site_structure_agent
from app.llm.llm_tool import LLMTool

logger = logging.getLogger(__name__)

# Dossier de stockage des projets generes (peut etre surcharge via env var).
STORAGE_DIR = Path(os.getenv("SITEGEN_STORAGE_DIR", "storage/sitegen_projects"))


class SiteGeneratorOrchestrator:
    """Orchestre le pipeline CDC text -> site HTML + ZIP + structure."""

    def __init__(self, llm: Optional[LLMTool] = None):
        self.llm = llm or LLMTool()

    def generate(self, cdc_text: str) -> Dict[str, Any]:
        project_id = uuid.uuid4().hex[:12]
        project_dir = STORAGE_DIR / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[Orchestrator] Demarrage pipeline - project_id=%s", project_id)

        # 1. Extraction structuree du CDC (LLM)
        cdc = cdc_parser_agent.parse_cdc(cdc_text, self.llm)

        # 2. Design system (deterministe)
        design = design_system_agent.generate_design_system(cdc.branding)

        # 3. Structure du site (deterministe)
        structure = site_structure_agent.generate_site_structure(cdc)

        # 4. Generation des fichiers HTML/CSS (deterministe)
        site_dir = html_generator.generate_site(cdc, design, structure, str(project_dir))

        # 5. Preview = contenu de index.html
        index_path = Path(site_dir) / "index.html"
        preview_html = index_path.read_text(encoding="utf-8") if index_path.exists() else ""

        # 6. ZIP du site genere
        zip_base = str(project_dir / "site")
        zip_path = shutil.make_archive(zip_base, "zip", site_dir)

        logger.info("[Orchestrator] Pipeline termine - project_id=%s", project_id)

        return {
            "project_id": project_id,
            "preview_html": preview_html,
            "site_dir": site_dir,
            "zip_path": zip_path,
            "structure": structure.model_dump(),
            "cdc": cdc.model_dump(),
            "design": design.model_dump(),
        }

    @staticmethod
    def get_zip_path(project_id: str) -> Path:
        """Chemin du ZIP genere pour un project_id donne."""
        return STORAGE_DIR / project_id / "site.zip"
