from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.services.style_extractor import extract_style_from_images

router = APIRouter(prefix="/style", tags=["Style Extractor"])

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


@router.post("/extract")
async def extract_style(files: List[UploadFile] = File(...)):
    """
    Reçoit 2-3 images de référence et retourne le style extrait.
    """
    if len(files) < 1:
        raise HTTPException(
            status_code=400,
            detail="Minimum 2 images requises pour l'extraction de style."
        )
    if len(files) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 images acceptées."
        )

    images = []
    for file in files:
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Format non supporté : {file.filename}. Utilisez PNG, JPG ou WebP."
            )
        content = await file.read()
        images.append((content, file.content_type))

    try:
        result = extract_style_from_images(images)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'extraction : {str(e)}")

    return result