import os
from dataclasses import dataclass
from typing import Any, Optional
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.files import FileMetadata, FolderMetadata
from dropbox.exceptions import AuthError, ApiError


APP_KEY    = os.getenv("DROPBOX_APP_KEY", "")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET", "")

# Stockage temporaire des flows OAuth (en prod : Redis ou DB)
_auth_flows: dict = {}


# ─── Data structure ───────────────────────────────────────────────────────────
@dataclass
class ServiceResult:
    is_success: bool
    data: Any = None
    message: str = ""

    @classmethod
    def success(cls, data):
        return cls(is_success=True, data=data)

    @classmethod
    def failure(cls, message):
        return cls(is_success=False, message=message)


# ─── Service ──────────────────────────────────────────────────────────────────
class DropboxService:
    def __init__(self, access_token: str = ""):
        self.access_token = access_token
        self._dbx: Optional[dropbox.Dropbox] = None
        if self.access_token:
            self._dbx = dropbox.Dropbox(
                oauth2_access_token=self.access_token,
                app_key=APP_KEY,
                app_secret=APP_SECRET,
            )

    # ── OAuth2 ────────────────────────────────────────────────────────────────
    @staticmethod
    def create_auth_flow(state: str) -> str:
        """Crée un flow OAuth2 PKCE et retourne l'URL d'autorisation."""
        flow = DropboxOAuth2FlowNoRedirect(
            consumer_key=APP_KEY,
            consumer_secret=APP_SECRET,
            token_access_type="offline",
            use_pkce=True,
        )
        auth_url = flow.start()
        _auth_flows[state] = flow
        return auth_url

    @staticmethod
    def exchange_code(state: str, code: str) -> "ServiceResult":
        """Échange le code d'autorisation contre l'access_token."""
        flow = _auth_flows.pop(state, None)
        if not flow:
            return ServiceResult.failure("State invalide ou expiré.")
        try:
            result = flow.finish(code)
            return ServiceResult.success({
                "access_token":  result.access_token,
                "refresh_token": result.refresh_token or "",
                "account_id":    result.account_id,
            })
        except Exception as e:
            return ServiceResult.failure(str(e))

    def _client(self) -> Optional[dropbox.Dropbox]:
        return self._dbx

    # ── List files ────────────────────────────────────────────────────────────
    def list_files(self, path: str = "", recursive: bool = False) -> "ServiceResult":
        dbx = self._client()
        if not dbx:
            return ServiceResult.failure("Non authentifié.")
        try:
            clean_path = "" if path in ("/", "") else path
            result = dbx.files_list_folder(clean_path, recursive=recursive)
            entries = list(result.entries)
            while result.has_more:
                result = dbx.files_list_folder_continue(result.cursor)
                entries += result.entries

            files = sorted(
                [self._parse(e) for e in entries],
                key=lambda f: (not f["is_folder"], f["name"].lower()),
            )
            return ServiceResult.success({"files": files, "total": len(files)})

        except AuthError:
            return ServiceResult.failure("Token invalide ou expiré.")
        except ApiError as e:
            return ServiceResult.failure(f"Dropbox API : {e.error}")
        except Exception as e:
            return ServiceResult.failure(str(e))

    # ── Search files ──────────────────────────────────────────────────────────
    def search_files(self, query: str, path: str = "") -> "ServiceResult":
        dbx = self._client()
        if not dbx:
            return ServiceResult.failure("Non authentifié.")
        try:
            clean_path = "" if path in ("/", "") else path
            options = dropbox.files.SearchOptions(
                path=clean_path or None,
                max_results=100,
                filename_only=False,
            )
            result = dbx.files_search_v2(query, options=options)
            entries = [m.metadata.get_metadata() for m in result.matches]
            files = [self._parse(e) for e in entries]
            return ServiceResult.success({"files": files, "total": len(files)})

        except AuthError:
            return ServiceResult.failure("Token invalide ou expiré.")
        except ApiError as e:
            return ServiceResult.failure(f"Dropbox API : {e.error}")
        except Exception as e:
            return ServiceResult.failure(str(e))

    # ── Download file ─────────────────────────────────────────────────────────
    def download_file(self, path: str) -> "ServiceResult":
        dbx = self._client()
        if not dbx:
            return ServiceResult.failure("Non authentifié.")
        try:
            metadata, response = dbx.files_download(path)
            content  = response.content
            filename = metadata.name
            ext      = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            mime_map = {
                "pdf":  "application/pdf",
                "jpg":  "image/jpeg", "jpeg": "image/jpeg",
                "png":  "image/png",  "gif":  "image/gif",
                "mp4":  "video/mp4",  "mp3":  "audio/mpeg",
                "zip":  "application/zip",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "csv":  "text/csv",
                "json": "application/json",
                "txt":  "text/plain",
            }
            return ServiceResult.success({
                "filename":     filename,
                "content":      content,
                "content_type": mime_map.get(ext, "application/octet-stream"),
                "size":         len(content),
            })

        except AuthError:
            return ServiceResult.failure("Token invalide ou expiré.")
        except ApiError as e:
            return ServiceResult.failure(f"Dropbox API : {e.error}")
        except Exception as e:
            return ServiceResult.failure(str(e))

    # ── Helper ────────────────────────────────────────────────────────────────
    @staticmethod
    def _parse(e) -> dict:
        return {
            "name":      e.name,
            "path":      e.path_lower or e.path_display or "",
            "size":      getattr(e, "size", 0) or 0,
            "modified":  str(getattr(e, "client_modified", "") or ""),
            "is_folder": isinstance(e, FolderMetadata),
            "id":        getattr(e, "id", "") or "",
        }