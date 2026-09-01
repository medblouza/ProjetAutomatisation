'''
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.web_code_generator import WebCodeGenerator
from app.schema.web_generator_schema import GeneratedSite


router = APIRouter(
    prefix="/api/web-generator",
    tags=["web-generator"]
)


class GenerateWebsiteRequest(BaseModel):
    design_json: Dict[str, Any]


_generator = WebCodeGenerator()


@router.post(
    "/generate",
    response_model=GeneratedSite
)
async def generate_website(
    body: GenerateWebsiteRequest
) -> GeneratedSite:

    try:
        return _generator.generate(body.design_json)

    except Exception as e:
        print("===== WEB GENERATOR ERROR =====")
        print(repr(e))

        raise HTTPException(
            status_code=502,
            detail=f"Website generation failed: {str(e)}"
        )
'''
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.services.web_code_generator import WebCodeGenerator
from app.schema.web_generator_schema import GeneratedSite

router = APIRouter(
    prefix="/api/web-generator",
    tags=["web-generator"]
)

_generator = WebCodeGenerator()


@router.post(
    "/generate",
    response_model=GeneratedSite
)
async def generate_website(
    design_json: Dict[str, Any]
) -> GeneratedSite:

    try:
        return _generator.generate(design_json)

    except Exception as e:
        print("===== WEB GENERATOR ERROR =====")
        print(repr(e))

        raise HTTPException(
            status_code=502,
            detail=f"Website generation failed: {str(e)}"
        )