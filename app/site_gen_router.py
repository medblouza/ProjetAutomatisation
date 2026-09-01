"""
app/api/sitegen_router.py

Endpoints FastAPI pour le pipeline de generation de site.

POST /site-generator/generate
  INPUT  : {"text": "<cahier des charges>"}
  OUTPUT : {"project_id", "preview_html", "download_url", "structure"}

GET /site-generator/download/{project_id}
  Retourne le ZIP du site genere.
"""
import logging
from fastapi import UploadFile, File
from pathlib import Path
import tempfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.mcp.agents.sitegen.orchestrator import SiteGeneratorOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

# Instance partagee de l'orchestrateur (LLMTool est reutilisable / stateless).
_orchestrator = SiteGeneratorOrchestrator()


class GenerateRequest(BaseModel):
    text: str = Field(..., description="Texte brut du cahier des charges (PDF/DOCX/TXT)")


class GenerateResponse(BaseModel):
    project_id: str
    preview_html: str
    download_url: str
    structure: dict
    cdc: dict


@router.post("/generate", response_model=GenerateResponse)
def generate_site(payload: GenerateRequest) -> GenerateResponse:
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Le champ 'text' ne peut pas etre vide.")

    try:
        result = _orchestrator.generate(payload.text)
    except Exception as exc:
        logger.exception("[SiteGenRouter] Erreur pendant la generation du site")
        raise HTTPException(status_code=500, detail=f"Erreur pipeline : {exc}") from exc

    return GenerateResponse(
        project_id=result["project_id"],
        preview_html=result["preview_html"],
        download_url=f"/download/{result['project_id']}",
        structure=result["structure"],
        cdc=result["cdc"],
    )


@router.get("/download/{project_id}")
def download_site(project_id: str) -> FileResponse:
    zip_path = SiteGeneratorOrchestrator.get_zip_path(project_id)

    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Projet introuvable ou expire.")

    return FileResponse(
        path=str(zip_path),
        media_type="application/zip",
        filename="site.zip",
    )

