import secrets
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.dropbox_service import DropboxService
from app.dropbox.asset_checker import analyze_asset, result_to_dict


dropbox_router = APIRouter(tags=["Dropbox"])


# ─── Models ───────────────────────────────────────────────────────────────────
class CallbackRequest(BaseModel):
    code: str
    state: str

class ListRequest(BaseModel):
    access_token: str
    path: str = ""
    recursive: bool = False

class SearchRequest(BaseModel):
    access_token: str
    query: str
    path: str = ""

class DownloadRequest(BaseModel):
    access_token: str
    path: str

class CheckAssetsRequest(BaseModel):
    access_token: str
    path: str = ""

# ─── Routes ───────────────────────────────────────────────────────────────────
@dropbox_router.get("/auth-url")
def get_auth_url():
    """Génère l'URL d'autorisation Dropbox."""
    state = secrets.token_urlsafe(16)
    auth_url = DropboxService.create_auth_flow(state)
    return {"auth_url": auth_url, "state": state}


@dropbox_router.post("/callback")
def callback(req: CallbackRequest):
    """Échange le code d'autorisation contre les tokens."""
    result = DropboxService.exchange_code(req.state, req.code)
    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.data


@dropbox_router.post("/list")
def list_files(req: ListRequest):
    """Liste les fichiers d'un dossier Dropbox."""
    svc = DropboxService(req.access_token)
    result = svc.list_files(req.path, req.recursive)
    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.data


@dropbox_router.post("/search")
def search_files(req: SearchRequest):
    """Recherche des fichiers par nom."""
    svc = DropboxService(req.access_token)
    result = svc.search_files(req.query, req.path)
    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)
    return result.data


@dropbox_router.post("/download")
def download_file(req: DownloadRequest):
    """Télécharge un fichier depuis Dropbox."""
    svc = DropboxService(req.access_token)
    result = svc.download_file(req.path)
    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.message)
    data = result.data
    return Response(
        content=data["content"],
        media_type=data["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{data["filename"]}"'},
    )

@dropbox_router.post("/check-assets")
def check_assets(req: CheckAssetsRequest):
    """Analyse tous les fichiers d'un dossier Dropbox."""
    svc = DropboxService(req.access_token)

    list_result = svc.list_files(req.path)
    if not list_result.is_success:
        raise HTTPException(status_code=400, detail=list_result.message)

    files   = [f for f in list_result.data.get("files", []) if not f.get("is_folder")]
    results = []

    for file in files:
        try:
            dl      = svc.download_file(file["path"])
            content = dl.data["content"] if dl.is_success else b""
            result  = analyze_asset(file, content)
            results.append(result_to_dict(result))
        except Exception as e:
            results.append({
                "name":         file.get("name", ""),
                "path":         file.get("path", ""),
                "status":       "error",
                "badge":        "⛔",
                "label":        "Bloqué",
                "issues":       [f"Erreur : {str(e)}"],
                "suggestions":  ["Vérifier le fichier manuellement"],
                "category":     "unknown",
                "needs_manual": True,
            })

    return {
        "total":        len(results),
        "ok":           sum(1 for r in results if r["status"] == "ok"),
        "warnings":     sum(1 for r in results if r["status"] == "warning"),
        "errors":       sum(1 for r in results if r["status"] == "error"),
        "needs_manual": sum(1 for r in results if r.get("needs_manual")),
        "assets":       results,
    }