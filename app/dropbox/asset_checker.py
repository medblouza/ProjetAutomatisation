"""
app/asset_checker.py
Auto-check assets Dropbox :
- Télécharge chaque fichier en mémoire (BytesIO)
- Détecte la catégorie par dimensions (PIL)
- Vérifie qualité selon la catégorie
- Retourne statut : validé / attention / bloqué
"""
import io
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from PIL import Image
import requests

# ── Constantes ────────────────────────────────────────────────────────────────

# Résolution minimale recommandée
MIN_DPI_WEB   = 72
MIN_DPI_PRINT = 150

# Dimensions pour catégorisation
ICON_MAX_SIZE    = 128    # px — icône si carré <= 128
LOGO_MAX_SIZE    = 600    # px — logo si carré <= 600
BANNER_MIN_WIDTH = 1000   # px — bannière si largeur >= 1000
BANNER_RATIO     = 2.0    # ratio w/h — bannière si ratio >= 2

# Extensions
VECTOR_EXT  = {".svg", ".ai", ".eps"}
IMAGE_EXT   = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tiff", ".bmp"}
VIDEO_EXT   = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
DOC_EXT     = {".pdf", ".docx", ".doc", ".pptx", ".xlsx"}

# Mots-clés nom fichier (bonus, pas principal)
LOGO_KEYWORDS   = {"logo", "logotype", "marque", "brand"}
ICON_KEYWORDS   = {"icon", "icone", "icône", "picto", "pictogramme"}
BANNER_KEYWORDS = {"banner", "banniere", "bannière", "hero", "header", "cover"}
DARK_KEYWORDS   = {"dark", "noir", "black", "sombre", "nuit"}
LIGHT_KEYWORDS  = {"light", "blanc", "white", "clair", "jour"}

# Poids max vidéo
MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200 Mo


# ── Dataclasses ───────────────────────────────────────────────────────────────
@dataclass
class CheckResult:
    name:          str
    path:          str
    extension:     str
    size:          int
    category:      str        # logo | icon | image | banner | video | svg | doc | unknown
    category_auto: bool       # True = détecté auto, False = incertain
    status:        str        # ok | warning | error
    badge:         str        # ✅ | ⚠️ | ⛔
    label:         str        # Validé | Attention | Bloqué
    dimensions:    Optional[Tuple[int, int]] = None
    issues:        List[str] = field(default_factory=list)
    suggestions:   List[str] = field(default_factory=list)
    needs_manual:  bool = False   # True = catégorie incertaine, demander à l'utilisateur


# ── Détection catégorie ───────────────────────────────────────────────────────
def _detect_category_from_name(name: str) -> Optional[str]:
    """Indice depuis le nom — peu fiable, utilisé en bonus."""
    n = name.lower().replace(" ", "").replace("-", "").replace("_", "")
    if any(k in n for k in LOGO_KEYWORDS):   return "logo"
    if any(k in n for k in ICON_KEYWORDS):   return "icon"
    if any(k in n for k in BANNER_KEYWORDS): return "banner"
    return None


def _detect_category_from_dimensions(w: int, h: int) -> Tuple[str, bool]:
    """
    Détecte la catégorie depuis les dimensions.
    Retourne (catégorie, certain).
    """
    is_square = abs(w - h) <= max(w, h) * 0.05  # 5% de tolérance
    ratio     = w / h if h > 0 else 1

    if is_square:
        if max(w, h) <= ICON_MAX_SIZE:
            return "icon", True
        if max(w, h) <= LOGO_MAX_SIZE:
            return "logo", True
        return "image", False   # carré grand — incertain

    if w >= BANNER_MIN_WIDTH and ratio >= BANNER_RATIO:
        return "banner", True

    if w >= BANNER_MIN_WIDTH:
        return "image", True

    return "image", False


def _detect_category(name: str, ext: str, img: Optional[Image.Image]) -> Tuple[str, bool]:
    """Combine dimensions + nom pour détecter la catégorie."""
    # SVG → logo ou icône (on analyse le XML plus tard)
    if ext == ".svg":
        name_cat = _detect_category_from_name(name)
        return name_cat or "svg", name_cat is not None

    # Vidéo
    if ext in VIDEO_EXT:
        return "video", True

    # Document
    if ext in DOC_EXT:
        return "doc", True

    # Image — utiliser dimensions
    if img is not None:
        w, h = img.size
        cat, certain = _detect_category_from_dimensions(w, h)

        # Confirmer avec le nom si incertain
        if not certain:
            name_cat = _detect_category_from_name(name)
            if name_cat:
                return name_cat, True
        return cat, certain

    # Fallback nom
    name_cat = _detect_category_from_name(name)
    return name_cat or "unknown", name_cat is not None


# ── Vérifications par catégorie ───────────────────────────────────────────────
def _check_logo(name: str, ext: str, img: Optional[Image.Image], size: int) -> Tuple[List, List]:
    issues, suggestions = [], []

    # Format vectoriel recommandé
    if ext not in VECTOR_EXT:
        if ext in IMAGE_EXT:
            issues.append(f"Logo en format raster ({ext}) — vectoriel recommandé")
            suggestions.append("Fournir une version SVG ou AI du logo")
        else:
            issues.append(f"Format {ext} non recommandé pour un logo")

    # Variantes clair/sombre
    name_lower = name.lower()
    has_dark  = any(k in name_lower for k in DARK_KEYWORDS)
    has_light = any(k in name_lower for k in LIGHT_KEYWORDS)
    if not has_dark and not has_light:
        suggestions.append("Prévoir une variante claire et une variante sombre du logo")

    # Résolution si raster
    if img is not None:
        w, h = img.size
        if max(w, h) < 200:
            issues.append(f"Logo trop petit ({w}x{h}px) — minimum 200px recommandé")
            suggestions.append("Fournir le logo en haute résolution")

        # Transparence
        if ext == ".png" and img.mode != "RGBA":
            issues.append("Logo PNG sans transparence (fond non transparent)")
            suggestions.append("Exporter le logo avec fond transparent (PNG RGBA)")

    return issues, suggestions


def _check_image(name: str, ext: str, img: Optional[Image.Image], size: int) -> Tuple[List, List]:
    issues, suggestions = [], []

    # Format optimisé
    if ext in (".tiff", ".bmp"):
        issues.append(f"Format {ext} non optimisé pour le web")
        suggestions.append("Convertir en WebP ou JPG pour le web")
    elif ext not in (".webp", ".jpg", ".jpeg", ".png"):
        suggestions.append("Préférer WebP pour les images web (meilleure compression)")

    if img is not None:
        w, h = img.size

        # Résolution minimale
        if w < 800 or h < 400:
            issues.append(f"Image petite ({w}x{h}px) — risque de flou sur grands écrans")
            suggestions.append("Fournir l'image en résolution supérieure (min 800px)")

        # DPI si disponible
        dpi = img.info.get("dpi")
        if dpi:
            dpi_val = dpi[0] if isinstance(dpi, tuple) else dpi
            if dpi_val < MIN_DPI_WEB:
                issues.append(f"Résolution trop faible ({dpi_val:.0f} dpi — min {MIN_DPI_WEB} dpi)")
                suggestions.append("Fournir l'image à 72 dpi minimum pour le web")

    # Poids
    if size > 5 * 1024 * 1024:
        issues.append(f"Image lourde ({size / (1024*1024):.1f} Mo) — impact performance")
        suggestions.append("Compresser l'image ou convertir en WebP")

    return issues, suggestions


def _check_banner(name: str, ext: str, img: Optional[Image.Image], size: int) -> Tuple[List, List]:
    issues, suggestions = [], []

    if img is not None:
        w, h = img.size
        if w < BANNER_MIN_WIDTH:
            issues.append(f"Bannière trop petite ({w}px) — minimum {BANNER_MIN_WIDTH}px")
            suggestions.append("Fournir la bannière en 1920x600px minimum")

    if ext in (".tiff", ".bmp"):
        issues.append(f"Format {ext} non optimisé pour le web")
        suggestions.append("Convertir en WebP ou JPG")

    if size > 10 * 1024 * 1024:
        issues.append(f"Bannière trop lourde ({size / (1024*1024):.1f} Mo)")
        suggestions.append("Compresser ou convertir en WebP")

    return issues, suggestions


def _check_icon(name: str, ext: str, img: Optional[Image.Image], size: int, content: bytes) -> Tuple[List, List]:
    issues, suggestions = [], []

    # SVG recommandé pour icônes
    if ext != ".svg":
        issues.append(f"Icône en format {ext} — SVG recommandé pour icônes")
        suggestions.append("Convertir en SVG pour une meilleure scalabilité")

    # Vérifier SVG
    if ext == ".svg" and content:
        svg_issues = _check_svg_consistency(content)
        issues.extend(svg_issues)
        if svg_issues:
            suggestions.append("Uniformiser les stroke-width et styles dans le SVG")

    if img is not None:
        w, h = img.size
        if abs(w - h) > 5:
            issues.append(f"Icône non carrée ({w}x{h}px) — dimensions carrées recommandées")
            suggestions.append("Redimensionner en format carré")

    return issues, suggestions


def _check_video(name: str, ext: str, size: int) -> Tuple[List, List]:
    issues, suggestions = [], []

    if ext not in (".mp4", ".webm"):
        issues.append(f"Format vidéo {ext} non optimisé pour le web")
        suggestions.append("Convertir en MP4 (H.264) ou WebM pour le web")

    if size > MAX_VIDEO_SIZE:
        issues.append(f"Vidéo trop lourde ({size / (1024*1024):.0f} Mo — max 200 Mo)")
        suggestions.append("Compresser la vidéo ou réduire la résolution")

    return issues, suggestions


def _check_svg_consistency(content: bytes) -> List[str]:
    """Vérifie la cohérence d'un SVG (stroke-width, style)."""
    issues = []
    try:
        root    = ET.fromstring(content.decode("utf-8", errors="ignore"))
        widths  = set()
        ns      = {"svg": "http://www.w3.org/2000/svg"}

        for elem in root.iter():
            style = elem.get("style", "")
            sw    = elem.get("stroke-width")

            # Extraire stroke-width depuis style=""
            m = re.search(r"stroke-width\s*:\s*([\d.]+)", style)
            if m:
                widths.add(round(float(m.group(1)), 1))
            if sw:
                try:
                    widths.add(round(float(sw), 1))
                except ValueError:
                    pass

        if len(widths) > 2:
            issues.append(f"Épaisseurs de trait incohérentes ({len(widths)} valeurs différentes : {widths})")

    except ET.ParseError:
        issues.append("SVG corrompu ou invalide — impossible à parser")
    except Exception:
        pass

    return issues


# ── Analyse principale ────────────────────────────────────────────────────────
def analyze_asset(file: dict, content: bytes) -> CheckResult:
    """
    Analyse complète d'un asset à partir de son contenu binaire.
    """
    name  = file.get("name", "")
    path  = file.get("path", "")
    size  = file.get("size", 0) or len(content)
    ext   = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""

    img: Optional[Image.Image] = None

    # Charger l'image en mémoire si possible
    if ext in IMAGE_EXT and content:
        try:
            img = Image.open(io.BytesIO(content))
            img.load()
        except Exception:
            img = None

    dimensions = tuple(img.size) if img else None

    # Détecter catégorie
    category, category_auto = _detect_category(name, ext, img)
    needs_manual = not category_auto and category not in ("video", "doc", "svg")

    # Vérifications selon catégorie
    issues, suggestions = [], []

    if category == "logo":
        issues, suggestions = _check_logo(name, ext, img, size)
    elif category == "image":
        issues, suggestions = _check_image(name, ext, img, size)
    elif category == "banner":
        issues, suggestions = _check_banner(name, ext, img, size)
    elif category == "icon":
        issues, suggestions = _check_icon(name, ext, img, size, content)
    elif category == "svg":
        svg_issues = _check_svg_consistency(content)
        issues.extend(svg_issues)
        if not svg_issues:
            suggestions.append("SVG valide — vérifier visuellement")
    elif category == "video":
        issues, suggestions = _check_video(name, ext, size)

    # Fichier vide
    if size == 0:
        issues.insert(0, "Fichier vide (0 octet)")
        suggestions.insert(0, "Vérifier que le fichier a bien été uploadé")

    # Statut final
    if issues:
        critical = any(
            kw in i.lower() for i in issues
            for kw in ["vide", "corrompu", "bloqué", "raster", "vectoriel"]
        )
        if critical:
            status, badge, label = "error",   "⛔", "Bloqué"
        else:
            status, badge, label = "warning", "⚠️", "Attention"
    else:
        status, badge, label = "ok", "✅", "Validé"

    return CheckResult(
        name=name, path=path, extension=ext, size=size,
        category=category, category_auto=category_auto,
        status=status, badge=badge, label=label,
        dimensions=dimensions,
        issues=issues, suggestions=suggestions,
        needs_manual=needs_manual,
    )


def result_to_dict(r: CheckResult) -> dict:
    return {
        "name":          r.name,
        "path":          r.path,
        "extension":     r.extension,
        "size":          r.size,
        "category":      r.category,
        "category_auto": r.category_auto,
        "needs_manual":  r.needs_manual,
        "status":        r.status,
        "badge":         r.badge,
        "label":         r.label,
        "dimensions":    list(r.dimensions) if r.dimensions else None,
        "issues":        r.issues,
        "suggestions":   r.suggestions,
    }