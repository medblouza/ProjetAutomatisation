"""
app/services/figma_service.py
Connexion à l'API REST Figma pour créer et mettre à jour des fichiers wireframe.
"""

import os
import httpx
from typing import Optional

FIGMA_TOKEN = os.getenv("FIGMA_TOKEN", "")
BASE_URL = "https://api.figma.com/v1"

HEADERS = {
    "X-Figma-Token": FIGMA_TOKEN,
    "Content-Type": "application/json",
}


# ──────────────────────────────────────────────
# Helpers HTTP
# ──────────────────────────────────────────────

def _get(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    r = httpx.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def _post(path: str, payload: dict) -> dict:
    url = f"{BASE_URL}{path}"
    r = httpx.post(url, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def _put(path: str, payload: dict) -> dict:
    url = f"{BASE_URL}{path}"
    r = httpx.put(url, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


# ──────────────────────────────────────────────
# API publique
# ──────────────────────────────────────────────

def verify_token() -> dict:
    """Vérifie que le token Figma est valide en récupérant le profil user."""
    return _get("/me")


def get_file(file_key: str) -> dict:
    """Récupère la structure complète d'un fichier Figma."""
    return _get(f"/files/{file_key}")


def get_file_url(file_key: str) -> str:
    """Retourne l'URL publique d'un fichier Figma."""
    return f"https://www.figma.com/file/{file_key}"


def get_file_embed_url(file_key: str) -> str:
    """Retourne l'URL embed (iframe) d'un fichier Figma."""
    return f"https://www.figma.com/embed?embed_host=share&url=https://www.figma.com/file/{file_key}"


def create_file(name: str, team_id: Optional[str] = None) -> dict:
    """
    Crée un nouveau fichier Figma vide via l'API Draft.
    Retourne { key, name, last_modified, ... }

    Note : l'API Figma ne permet pas de créer un fichier directement.
    On passe par la création d'un projet draft (POST /v1/teams/{id}/projects
    puis POST /v1/projects/{id}/files) — OU on utilise l'endpoint
    /v1/files (Figma for Teams uniquement).

    Stratégie utilisée ici : création via plugin REST (Drafts).
    Si team_id est fourni → crée dans l'équipe, sinon → draft personnel.
    """
    if team_id:
        # Crée un projet Figma dans l'équipe puis un fichier dedans
        proj = _post(f"/teams/{team_id}/projects", {"name": name})
        project_id = proj["id"]
        file_resp = _post(f"/projects/{project_id}/files", {"name": name})
    else:
        # Draft personnel — endpoint simplifié Figma REST API
        file_resp = _post("/files", {"name": name})

    return file_resp


def update_file(file_key: str, nodes: list[dict]) -> dict:
    """
    Met à jour le contenu d'un fichier Figma en appliquant une liste de nodes.
    Chaque node suit le schéma de l'API Figma (FRAME, TEXT, RECTANGLE…).

    nodes = [
        {
            "type": "FRAME",
            "name": "Homepage",
            "absoluteBoundingBox": {"x": 0, "y": 0, "width": 1440, "height": 900},
            "children": [ ... ]
        }
    ]
    """
    payload = {
        "nodes": nodes,
        "version_title": "WireframeAgent auto-generated",
    }
    return _put(f"/files/{file_key}", payload)


def create_wireframe_file(
    project_name: str,
    pages: list[dict],
    team_id: Optional[str] = None,
) -> dict:
    """
    Fonction de haut niveau : crée un fichier Figma et y injecte les pages
    générées par le WireframeAgent.

    pages = [
        {
            "name": "Accueil",
            "sections": [
                {"name": "Hero", "type": "hero", "width": 1440, "height": 600},
                {"name": "Services", "type": "grid", "width": 1440, "height": 400},
            ]
        },
        ...
    ]

    Retourne { file_key, file_url, embed_url }
    """
    # 1. Création du fichier
    file_resp = create_file(name=project_name, team_id=team_id)
    file_key = file_resp.get("key") or file_resp.get("id")

    if not file_key:
        raise ValueError(f"Impossible de récupérer la clé du fichier Figma : {file_resp}")

    # 2. Construction des nodes Figma depuis les pages
    nodes = _pages_to_figma_nodes(pages)

    # 3. Update du fichier avec le contenu
    update_file(file_key, nodes)

    return {
        "file_key": file_key,
        "file_url": get_file_url(file_key),
        "embed_url": get_file_embed_url(file_key),
        "name": project_name,
    }


# ──────────────────────────────────────────────
# Helpers internes : conversion pages → nodes
# ──────────────────────────────────────────────

_SECTION_HEIGHTS = {
    "hero": 600,
    "navbar": 80,
    "footer": 200,
    "grid": 400,
    "cta": 200,
    "form": 350,
    "text": 250,
    "gallery": 450,
    "default": 300,
}

_SECTION_COLOR = {
    "hero": {"r": 0.12, "g": 0.12, "b": 0.95, "a": 0.08},
    "navbar": {"r": 0.05, "g": 0.05, "b": 0.05, "a": 0.9},
    "footer": {"r": 0.15, "g": 0.15, "b": 0.15, "a": 0.85},
    "cta": {"r": 0.9, "g": 0.4, "b": 0.1, "a": 0.15},
    "default": {"r": 0.88, "g": 0.88, "b": 0.92, "a": 1.0},
}


def _section_to_frame(section: dict, y_offset: int, page_width: int = 1440) -> dict:
    section_type = section.get("type", "default").lower()
    height = section.get("height") or _SECTION_HEIGHTS.get(section_type, _SECTION_HEIGHTS["default"])
    color = _SECTION_COLOR.get(section_type, _SECTION_COLOR["default"])

    label_node = {
        "type": "TEXT",
        "name": "label",
        "characters": section.get("name", section_type.upper()),
        "absoluteBoundingBox": {
            "x": 40, "y": y_offset + 20, "width": page_width - 80, "height": 40
        },
        "style": {"fontSize": 24, "fontWeight": "Bold"},
        "fills": [{"type": "SOLID", "color": {"r": 0.2, "g": 0.2, "b": 0.2, "a": 1}}],
    }

    return {
        "type": "FRAME",
        "name": section.get("name", section_type.capitalize()),
        "absoluteBoundingBox": {
            "x": 0, "y": y_offset, "width": page_width, "height": height
        },
        "fills": [{"type": "SOLID", "color": color}],
        "clipsContent": True,
        "children": [label_node],
    }


def _pages_to_figma_nodes(pages: list[dict], page_width: int = 1440) -> list[dict]:
    """Convertit la structure pages → liste de FRAME nodes Figma."""
    nodes = []
    for page_idx, page in enumerate(pages):
        y_offset = 0
        page_children = []

        for section in page.get("sections", []):
            frame = _section_to_frame(section, y_offset, page_width)
            h = frame["absoluteBoundingBox"]["height"]
            y_offset += h + 20  # gap entre sections
            page_children.append(frame)

        page_node = {
            "type": "FRAME",
            "name": page.get("name", f"Page {page_idx + 1}"),
            "absoluteBoundingBox": {
                "x": page_idx * (page_width + 200),
                "y": 0,
                "width": page_width,
                "height": y_offset,
            },
            "fills": [{"type": "SOLID", "color": {"r": 1, "g": 1, "b": 1, "a": 1}}],
            "clipsContent": False,
            "children": page_children,
        }
        nodes.append(page_node)

    return nodes