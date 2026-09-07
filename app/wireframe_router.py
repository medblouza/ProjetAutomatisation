from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Any
import os

from app.mcp.agents.wireframe_agent import WireframeAgent

router = APIRouter()


class WireframeRequest(BaseModel):
    cleaned_data: dict[str, Any]
    team_id: Optional[str] = None  # conservé pour compatibilité, non utilisé


class WireframeResponse(BaseModel):
    html: str
    project_name: str
    pages: list[dict]
    style: dict
    pages_count: int


@router.post("/generate-wireframe", response_model=WireframeResponse)
async def generate_wireframe(req: WireframeRequest):
    """
    Génère un wireframe HTML à partir des données nettoyées (sortie cleaner.py).
    Retourne le HTML complet + la structure des pages.
    """
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY non configuré")

    try:
        agent  = WireframeAgent()
        result = agent.run(cleaned_data=req.cleaned_data)
        return WireframeResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération wireframe : {e}")


@router.get("/wireframe-preview/{project_name}", response_class=HTMLResponse)
async def wireframe_preview(project_name: str):
    """Endpoint optionnel pour prévisualiser un wireframe stocké en session."""
    return HTMLResponse("<p>Utilise l'onglet Streamlit pour prévisualiser le wireframe.</p>")