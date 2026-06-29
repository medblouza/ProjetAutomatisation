'''
import os, tempfile, logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from app.llm.llm_tool import LLMTool
from app.services.file_parser import FileParser
from app.mcp.agents.sitegen.site_analyzer_agent import SiteAnalyzerAgent
from app.mcp.agents.sitegen.orchestrator        import SiteGenOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
_llm   = LLMTool()


@router.post("/analyze")
async def analyze_cdc(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "upload.txt")[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        raw  = FileParser().parse(tmp_path)
        return SiteAnalyzerAgent(_llm).run(raw)
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        os.unlink(tmp_path)


@router.post("/generate")
async def generate_site(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "upload.txt")[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    output_dir = tempfile.mkdtemp()
    try:
        raw    = FileParser().parse(tmp_path)
        result = SiteGenOrchestrator(_llm).run(raw, output_dir)
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        os.unlink(tmp_path)
    if "error" in result:
        raise HTTPException(422, result["error"])
    return result


@router.get("/download")
async def download_zip(zip_path: str):
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(404, "ZIP introuvable")
    return FileResponse(zip_path, media_type="application/zip",
                        filename="generated_site.zip")
'''