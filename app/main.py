
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.dp_service import DpService
from app.cleaner import clean_dp_data
from app.llm.llm_tool import LLMTool
from app.mcp.agents.base_agent import BaseAgent

app = FastAPI(title="DP Service API")

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
    result = service.process_codesage(req.code)

    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)

    raw = result.data

    pipeline = BaseAgent(LLMTool())
    output = pipeline.run(raw)

    return output