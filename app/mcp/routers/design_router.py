"""
Design pipeline router — Phase 1 exposes CDC analysis only.
Phase 2 will add /api/design/generate (Design Director Agent -> DesignJSON).
Phase 3 will add /api/design/export (-> Figma plugin payload).
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.mcp.agents.sitegen.cdc_analyzer_agent import CDCAnalyzerAgent
from app.schema.cdc_schema import CDCAnalysis
from app.services.file_extraction_service import (
    UnsupportedFileTypeError,
    extract_text_from_upload,
)
from app.services.llm_service import LLMGenerationError


from app.schema.design_schema import DesignJSON
from app.mcp.agents.sitegen.design_generator_agent import DesignGeneratorAgent

_design_agent = DesignGeneratorAgent()


router = APIRouter(prefix="/api", tags=["design-pipeline"])

_agent = CDCAnalyzerAgent()


class AnalyzeTextRequest(BaseModel):
    text: str


@router.post("/cdc/analyze", response_model=CDCAnalysis)
async def analyze_cdc_file(file: UploadFile = File(...)) -> CDCAnalysis:
    """Upload a CDC file (.pdf, .docx, .txt, .md) and get back a structured
    CDCAnalysis JSON."""
    try:
        text = await extract_text_from_upload(file)
    except UnsupportedFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    try:
        return _agent.analyze(text)
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.post("/cdc/analyze-text", response_model=CDCAnalysis)
async def analyze_cdc_text(body: AnalyzeTextRequest) -> CDCAnalysis:
    """Same as /cdc/analyze but takes raw text directly — useful for testing
    from the frontend without a file, or for pasted CDC content."""
    try:
        return _agent.analyze(body.text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e




import json
import logging
from app.database import save_design_json

logger = logging.getLogger(__name__)

@router.post("/design/generate", response_model=DesignJSON)
async def generate_design(body: CDCAnalysis) -> DesignJSON:
    """Takes the CDCAnalysis JSON (output of /cdc/analyze) and generates the
    full DesignJSON: theme, palette, typography, and per-page components."""
    try:
        design = _design_agent.generate(body)

        # ── Sauvegarde automatique PostgreSQL ──
        try:
            company_name = (
                (design.project.name if getattr(design, "project", None) and design.project.name else None)
                or (body.business_info.company_name if getattr(body, "business_info", None) and body.business_info.company_name else None)
                or "Entreprise inconnue"
            )
            json_str = json.dumps(design.model_dump(), indent=2, ensure_ascii=False)
            filename = f"{company_name.lower().replace(' ', '_')}_design.json"
            save_design_json(
                filename=filename,
                company_name=company_name,
                content=json_str,
            )
            logger.info(f"[DB] DesignJSON sauvegardé avec succès pour '{company_name}'")
        except Exception as db_err:
            logger.warning(f"[DB] Échec de la sauvegarde automatique DesignJSON : {db_err}")

        return design
    except LLMGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.post("/design/generate-file", response_model=DesignJSON)
async def generate_design_from_file(file: UploadFile = File(...)):
    try:
        print("\n==============================")
        print("STEP 1 - EXTRACTION DU CDC")
        print("==============================")

        text = await extract_text_from_upload(file)

        print(f"Text extracted successfully")
        print(f"Text length: {len(text)} characters")

        print("\n==============================")
        print("STEP 2 - CDC ANALYSIS")
        print("==============================")

        cdc = _agent.analyze(text)

        print("CDC ANALYSIS SUCCESS")
        print(f"Company: {cdc.business_info.company_name}")
        print(f"Sector: {cdc.business_info.sector}")
        print(f"Pages: {len(cdc.pages)}")

        print("\n==============================")
        print("STEP 3 - DESIGN GENERATION")
        print("==============================")

        design = _design_agent.generate(cdc)

        print("DESIGN GENERATION SUCCESS")

        # ── Sauvegarde automatique PostgreSQL ──
        try:
            company_name = (
                (design.project.name if getattr(design, "project", None) and design.project.name else None)
                or (cdc.business_info.company_name if getattr(cdc, "business_info", None) and cdc.business_info.company_name else None)
                or "Entreprise inconnue"
            )
            json_str = json.dumps(design.model_dump(), indent=2, ensure_ascii=False)
            save_design_json(
                filename=file.filename or "design.json",
                company_name=company_name,
                content=json_str,
            )
            logger.info(f"[DB] DesignJSON sauvegardé avec succès pour '{company_name}' ({file.filename})")
            print(f"[DB] DesignJSON sauvegardé avec succès pour '{company_name}' ({file.filename})")
        except Exception as db_err:
            logger.warning(f"[DB] Échec de la sauvegarde automatique DesignJSON : {db_err}")
            print(f"[DB] Échec de la sauvegarde automatique DesignJSON : {db_err}")

        return design

    except UnsupportedFileTypeError as e:
        print(f"FILE ERROR: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except LLMGenerationError as e:
        print(f"LLM ERROR: {e}")
        raise HTTPException(
            status_code=502,
            detail=str(e)
        )

    except Exception as e:
        print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


