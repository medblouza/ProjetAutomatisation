"""
app/agents/design_system_agent.py
Logique deterministe : construit le design system depuis le branding du CDC.
"""
import logging
from app.mcp.agents.sitegen.schemas import Branding, ColorPalette, DesignSystem, Fonts, Radius, Spacing

logger = logging.getLogger(__name__)

DEFAULT_PRIMARY    = "#2563eb"
DEFAULT_SECONDARY  = "#64748b"
DEFAULT_BACKGROUND = "#ffffff"
DEFAULT_FONT       = "Inter"

STYLE_FONT_MAP = {
    "moderne":        "Inter",
    "minimaliste":    "Inter",
    "epure":          "Inter",
    "elegant":        "Playfair Display",
    "elegante":       "Playfair Display",
    "luxe":           "Playfair Display",
    "vintage":        "Playfair Display",
    "epure vintage":  "Playfair Display",
    "corporate":      "Roboto",
    "professionnel":  "Roboto",
    "creatif":        "Poppins",
    "tech":           "Space Grotesk",
}


def _is_hex_color(value: str) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip()
    return v.startswith("#") and len(v) in (4, 7)


def _normalize_style(style: str) -> str:
    return (style or "").strip().lower()


def generate_design_system(branding: Branding) -> DesignSystem:
    valid_colors = [c for c in (branding.colors or []) if _is_hex_color(c)]

    primary    = valid_colors[0] if len(valid_colors) >= 1 else DEFAULT_PRIMARY
    secondary  = valid_colors[1] if len(valid_colors) >= 2 else DEFAULT_SECONDARY
    background = valid_colors[2] if len(valid_colors) >= 3 else DEFAULT_BACKGROUND

    # Typographie : champ explicite > mapping style > defaut
    typography = (branding.typography or "").strip()
    if typography:
        font = typography
    else:
        style_key = _normalize_style(branding.style)
        # cherche d'abord une cle composite (ex "epure vintage"), puis simple
        font = (
            STYLE_FONT_MAP.get(style_key)
            or next((v for k, v in STYLE_FONT_MAP.items() if k in style_key), None)
            or DEFAULT_FONT
        )

    design = DesignSystem(
        colors=ColorPalette(primary=primary, secondary=secondary, background=background),
        fonts=Fonts(main=font),
        spacing=Spacing(base="8px"),
        radius=Radius(small="4px", medium="8px"),
    )
    logger.info(
        "[DesignSystem] primary=%s secondary=%s background=%s font=%s",
        primary, secondary, background, font,
    )
    return design
