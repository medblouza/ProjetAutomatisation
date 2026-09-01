"""
cdc_router.py — Router FastAPI pour l'onglet CDC / JSON.

Endpoints CDC :
  GET    /api/cdc        → liste de tous les CDC (sans contenu)
  GET    /api/cdc/{id}   → CDC complet avec contenu
  POST   /api/cdc        → créer un nouveau CDC
  PUT    /api/cdc/{id}   → modifier un CDC existant
  DELETE /api/cdc/{id}   → supprimer un CDC

Endpoints DesignJSON :
  GET    /api/design-jsons        → liste de tous les DesignJSON (sans contenu)
  GET    /api/design-jsons/{id}   → DesignJSON complet avec contenu
  POST   /api/design-jsons        → créer un nouveau DesignJSON
  PUT    /api/design-jsons/{id}   → modifier un DesignJSON existant
  DELETE /api/design-jsons/{id}   → supprimer un DesignJSON
"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.database import (
    get_all_cdc,
    get_cdc_by_id,
    save_cdc,
    update_cdc,
    delete_cdc,
    get_all_design_jsons,
    get_design_json_by_id,
    save_design_json,
    update_design_json,
    delete_design_json,
)

router = APIRouter(prefix="/api/cdc", tags=["CDC"])
design_json_router = APIRouter(prefix="/api/design-jsons", tags=["DesignJSON"])


# ─────────────────────────────────────────────────────────────
# Modèles Pydantic
# ─────────────────────────────────────────────────────────────

class CDCRequest(BaseModel):
    company_name: str = Field(..., min_length=1, description="Nom de l'entreprise ou code client")
    content: str = Field(..., min_length=1, description="Contenu Markdown du CDC")


class DesignJsonRequest(BaseModel):
    filename: str = Field(default="design.json", description="Nom du fichier source")
    company_name: str = Field(..., min_length=1, description="Nom de l'entreprise")
    content: str = Field(..., min_length=1, description="Contenu JSON (texte sérialisé)")


# ─────────────────────────────────────────────────────────────
# CRUD CDC
# ─────────────────────────────────────────────────────────────

@router.get("")
def list_cdc():
    """
    Retourne la liste de tous les CDC stockés dans PostgreSQL.
    Chaque entrée contient : id, company_name, created_at.
    """
    records = get_all_cdc()
    return {"cdcs": records, "total": len(records)}


@router.get("/{cdc_id}")
def get_cdc(cdc_id: int):
    """
    Retourne le CDC complet (avec contenu Markdown) pour un id donné.
    """
    record = get_cdc_by_id(cdc_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"CDC introuvable (id={cdc_id})")
    return record


@router.post("", status_code=201)
def create_cdc(body: CDCRequest):
    """
    Crée un nouveau CDC dans PostgreSQL.
    """
    record = save_cdc(company_name=body.company_name, content=body.content)
    if not record:
        raise HTTPException(status_code=500, detail="Échec de l'enregistrement du CDC en base de données.")
    return {
        "id": record.id,
        "company_name": record.company_name,
        "content": record.content,
        "created_at": record.created_at.isoformat(),
    }


@router.put("/{cdc_id}")
def update_cdc_endpoint(cdc_id: int, body: CDCRequest):
    """
    Met à jour un CDC existant.
    """
    updated = update_cdc(cdc_id=cdc_id, company_name=body.company_name, content=body.content)
    if not updated:
        raise HTTPException(status_code=404, detail=f"CDC introuvable ou mise à jour échouée (id={cdc_id})")
    return updated


@router.delete("/{cdc_id}")
def delete_cdc_endpoint(cdc_id: int):
    """
    Supprime un CDC existant.
    """
    success = delete_cdc(cdc_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"CDC introuvable ou suppression impossible (id={cdc_id})")
    return {"status": "success", "message": f"CDC #{cdc_id} supprimé avec succès."}


# ─────────────────────────────────────────────────────────────
# CRUD DesignJSON
# ─────────────────────────────────────────────────────────────

@design_json_router.get("")
def list_design_jsons():
    """
    Retourne la liste de tous les DesignJSON stockés dans PostgreSQL.
    Chaque entrée contient : id, filename, company_name, created_at.
    """
    records = get_all_design_jsons()
    return {"design_jsons": records, "total": len(records)}


@design_json_router.get("/{record_id}")
def get_design_json(record_id: int):
    """
    Retourne le DesignJSON complet (avec contenu JSON) pour un id donné.
    """
    record = get_design_json_by_id(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"DesignJSON introuvable (id={record_id})")
    return record


@design_json_router.post("", status_code=201)
def create_design_json(body: DesignJsonRequest):
    """
    Crée un nouveau DesignJSON dans PostgreSQL.
    """
    # Validation du format JSON
    try:
        parsed = json.loads(body.content)
        formatted_content = json.dumps(parsed, indent=2, ensure_ascii=False)
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Le contenu fourni n'est pas un JSON valide : {str(err)}")

    record = save_design_json(
        filename=body.filename,
        company_name=body.company_name,
        content=formatted_content,
    )
    if not record:
        raise HTTPException(status_code=500, detail="Échec de l'enregistrement du DesignJSON en base.")
    return {
        "id": record.id,
        "filename": record.filename,
        "company_name": record.company_name,
        "content": record.content,
        "created_at": record.created_at.isoformat(),
    }


@design_json_router.put("/{record_id}")
def update_design_json_endpoint(record_id: int, body: DesignJsonRequest):
    """
    Met à jour un DesignJSON existant.
    """
    # Validation du format JSON
    try:
        parsed = json.loads(body.content)
        formatted_content = json.dumps(parsed, indent=2, ensure_ascii=False)
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Le contenu fourni n'est pas un JSON valide : {str(err)}")

    updated = update_design_json(
        record_id=record_id,
        filename=body.filename,
        company_name=body.company_name,
        content=formatted_content,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"DesignJSON introuvable ou mise à jour échouée (id={record_id})")
    return updated


@design_json_router.delete("/{record_id}")
def delete_design_json_endpoint(record_id: int):
    """
    Supprime un DesignJSON existant.
    """
    success = delete_design_json(record_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"DesignJSON introuvable ou suppression impossible (id={record_id})")
    return {"status": "success", "message": f"DesignJSON #{record_id} supprimé avec succès."}


