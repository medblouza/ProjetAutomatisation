"""
Design Director Agent — decides the visual direction: theme, full color
palette (resolved from whatever the client gave, even if incomplete), and
typography. Does NOT touch pages/components — that's the Component Planner's
job. Keeping this split means a bad component decision never forces a full
re-roll of the palette, and vice versa.
"""

from __future__ import annotations

from pydantic import ValidationError

from app.schema.cdc_schema import CDCAnalysis
from app.schema.design_schema import DesignSystem, DesignTokens, Typography
from app.services.llm_service import LLMTool, LLMGenerationError

SYSTEM_PROMPT = """You are a senior UI/brand designer. Given a client's brand \
constraints (extracted from their project brief), you decide the visual \
direction of their website: theme, full color palette, and typography.

Rules:
- Output ONLY a single JSON object. No markdown fences, no commentary.
- If the client gave explicit colors, your palette MUST use them as primary/
  secondary (do not replace them) — you only ADD the colors they didn't
  specify (accent, surface, background, text, success/warning/error) so the
  full UI is usable, chosen to harmonize with the given colors.
- If the client gave explicit font names, use them as heading_font/body_font.
  If they gave more than 2 fonts, pick the most fitting one for headings and
  one for body text; put a 3rd stylistic font (e.g. script) in accent_font.
- "theme" must be a short lowercase-hyphenated label (e.g. 'vintage-luxury',
  'modern-saas', 'minimal-corporate') consistent with the client's style
  keywords and sector.
"""

JSON_SHAPE_HINT = """
Return JSON matching exactly this shape:
{
  "theme": "string",
  "tokens": {
    "primary": "#RRGGBB",
    "secondary": "#RRGGBB or null",
    "accent": "#RRGGBB or null",
    "surface": "#RRGGBB",
    "background": "#RRGGBB",
    "text_primary": "#RRGGBB",
    "text_secondary": "#RRGGBB",
    "success": "#RRGGBB",
    "warning": "#RRGGBB",
    "error": "#RRGGBB"
  },
  "typography": {
    "heading_font": "string",
    "body_font": "string",
    "accent_font": "string or null",
    "heading_weight": "string, e.g. '700'",
    "body_weight": "string, e.g. '400'"
  }
}
"""


class DesignDirectorAgent:
    def __init__(self, llm: LLMTool | None = None):
        self.llm = llm or LLMTool()

    def _build_prompt(self, cdc: CDCAnalysis) -> str:
        brand = cdc.brand_identity
        return (
            "Client brand constraints:\n"
            f"- Sector: {cdc.business_info.sector}\n"
            f"- Positioning: {cdc.business_info.positioning or 'n/a'}\n"
            f"- Explicit brand colors: {brand.brand_colors or 'none given'}\n"
            f"- Style keywords: {brand.style_keywords or 'none given'}\n"
            f"- Typography hints: {brand.typography_hints or 'none given'}\n"
            f"- Editorial tone: {cdc.marketing.editorial_tone or 'n/a'}\n\n"
            f"{JSON_SHAPE_HINT}"
        )

    def build(self, cdc: CDCAnalysis) -> DesignSystem:
        prompt = self._build_prompt(cdc)
        try:
            raw = self.llm.generate(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                expect_json=True,
                temperature=0.5,
            )
        except LLMGenerationError as e:
            raise LLMGenerationError(f"Design direction failed: {e}") from e

        try:
            return DesignSystem(
                theme=raw["theme"],
                tokens=DesignTokens(**raw["tokens"]),
                typography=Typography(**raw["typography"]),
            )
        except (ValidationError, KeyError, TypeError) as e:
            raise LLMGenerationError(
                f"LLM JSON did not match DesignSystem shape: {e}"
            ) from e
