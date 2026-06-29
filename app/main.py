from dotenv import load_dotenv
import os
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.social_suggester import suggest_social
from app.dp_service import DpService
from app.cleaner import clean_dp_data
from app.llm.llm_tool import LLMTool
from app.mcp.agents.base_agent import BaseAgent
from app.dropbox_router import dropbox_router
from app.wireframe_router import router as wireframe_router
from app.style_extractor_router import router as style_extractor_router
from app.design_router import router as design_router
from fastapi.middleware.cors import CORSMiddleware
from app.site_gen_router import router as site_gen_router

app = FastAPI(title="DP Service API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # DEV ONLY
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(style_extractor_router, prefix="/api", tags=["Style Extractor"])
app.include_router(dropbox_router, prefix="/dropbox")
app.include_router(wireframe_router, prefix="/api", tags=["Wireframe"])
app.include_router(design_router)
app.include_router(site_gen_router, prefix="/api/site-gen", tags=["Site Generator"])

# ─────────────────────────────
# Models (inputs API)
# ─────────────────────────────
class AuthRequest(BaseModel):
    username: str
    password: str

class CodeRequest(BaseModel):
    username: str
    password: str
    code: str


# ─────────────────────────────
# Endpoint : test login
# ─────────────────────────────
@app.post("/login")
def login(req: AuthRequest):
    service = DpService(req.username, req.password)

    if service.login():
        return {"status": "success", "message": "Login OK"}
    raise HTTPException(status_code=401, detail="Login failed")


# ─────────────────────────────
# Endpoint : get_info_by_code
# ─────────────────────────────
@app.post("/info")
def get_info(req: CodeRequest):
    service = DpService(req.username, req.password)

    result = service.get_info_by_code(req.code)

    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.data


# ─────────────────────────────
# Endpoint : process_codesage
# ─────────────────────────────
@app.post("/process")
def process(req: CodeRequest):
    service = DpService(req.username, req.password)

    result = service.process_codesage(req.code)

    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)

    return result.data

# ─────────────────────────────
# Endpoint : clean data
# ─────────────────────────────
@app.post("/clean")
def clean(req: CodeRequest):
    service = DpService(req.username, req.password)

    result = service.get_info_by_code(req.code)

    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)

    raw_data = result.data

    cleaned = clean_dp_data(raw_data)

    return {
        "cleaned": cleaned
    }

@app.post("/generate-cdc")
def generate_cdc(req: CodeRequest):

    service = DpService(req.username, req.password)
    result  = service.get_info_by_code(req.code)  # ← get_info pas process

    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)

    cleaned  = clean_dp_data(result.data)          # ← nettoyage d'abord
    pipeline = BaseAgent(LLMTool())
    output   = pipeline.run(cleaned)               # ← pipeline sur données nettoyées

    content = output.get("content", "")
    score   = output.get("score", 0)

    if isinstance(content, list):
        content = "\n".join([str(x) for x in content])
    else:
        content = str(content)

    try:
        score = int(score)
    except:
        score = 0

    return {"content": content, "score": score}
@app.post("/suggest-social")
def suggest_social_api(data: dict):

    try:
        result = suggest_social(data)
        return {"suggestions": result}

    except Exception as e:
        return {"error": str(e)}