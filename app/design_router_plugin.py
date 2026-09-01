# app/design_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.mcp.agents.design_generator_agent import DesignGeneratorAgent
from app.dp_service import DpService
from app.services.design_data_adapter import adapt_for_design

router = APIRouter(prefix="/api/design", tags=["Design"])
agent = DesignGeneratorAgent()

class GenerateRequest(BaseModel):
    username: str
    password: str
    client_code: str

@router.post("/generate")
async def generate_design(req: GenerateRequest):
    """
    Récupère les données DP, génère et retourne le DESIGN JSON.
    Le plugin Figma appelle cet endpoint directement.
    """
    # 1. Récupérer depuis DP — même pattern que tes endpoints existants
    dp = DpService(req.username, req.password)
    result = dp.get_info_by_code(req.client_code)
    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)

    # 2. Adapter les données pour l'agent
    design_input = adapt_for_design(result.data, req.client_code)

    # 3. Générer le DESIGN JSON via Groq
    design = agent.run(design_input)

    # 4. Retourner directement — pas de stockage
    return design.model_dump()