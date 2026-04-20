from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.dp_service import DpService

router = APIRouter()

# ─────────────────────────────
# INPUT MODEL
# ─────────────────────────────
class RequestModel(BaseModel):
    username: str
    password: str
    code: str


# ─────────────────────────────
# TOOL 1 - GET INFO
# ─────────────────────────────
@router.post("/tools/get-info")
def get_info(req: RequestModel):
    service = DpService(req.username, req.password)

    result = service.get_info_by_code(req.code)

    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)

    return {
        "tool": "get_info",
        "result": result.data
    }


# ─────────────────────────────
# TOOL 2 - PROCESS CODE SAGE
# ─────────────────────────────
@router.post("/tools/process")
def process(req: RequestModel):
    service = DpService(req.username, req.password)

    result = service.process_codesage(req.code)

    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)

    return {
        "tool": "process_codesage",
        "result": result.data
    }