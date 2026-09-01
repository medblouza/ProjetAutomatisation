"""
CDCAnalyzerAgent — turns raw CDC text (extracted from PDF/DOCX/TXT) into a
validated CDCAnalysis object.

This agent does ONE job: understand what the client is asking for. It must
NOT make any visual/design decision — that is the DesignDirectorAgent's job
(Phase 2). Keeping this boundary is what lets the pipeline stay modular:
    raw text -> CDCAnalysis -> (later) DesignJSON
"""

from __future__ import annotations

from pydantic import ValidationError

from app.schema.cdc_schema import CDCAnalysis
from app.services.llm_service import LLMTool, LLMGenerationError

SYSTEM_PROMPT = """You are a business analyst that reads a client's project brief \
(Cahier des Charges) and extracts a structured summary of their needs.

Rules:
- Output ONLY a single JSON object. No markdown fences, no commentary, no explanations.
- Never invent information that is not implied by the text. If something is not \
mentioned, omit it or use an empty value/list — do not hallucinate specifics.
- Do NOT make any NEW visual/design decisions. Only capture design constraints the \
client ALREADY gave (hex colors, style keywords like 'vintage', font names). Never \
invent a color or font that isn't in the source text.
- For each page, "content" must be the marketing copy VERBATIM from the CDC if present \
(do not summarize or rewrite it) — this text will be reused as real site content later.
- "pages" must contain at least one page. If the CDC has an explicit page list \
(arborescence), use it exactly — same names, same order, same URLs.
- "sections" per page come from the "Sections à intégrer" list if present.
"""

JSON_SHAPE_HINT = """
Return JSON matching exactly this shape:
{
  "business_info": {
    "company_name": "string",
    "sector": "string",
    "city": "string or null",
    "service_area": "string or null",
    "target_audience": "string or null",
    "differentiators": ["string"],
    "experience": "string or null",
    "value_proposition": "string or null",
    "positioning": "string or null"
  },
  "marketing": {
    "objectives": ["string"],
    "key_messages": ["string"],
    "editorial_tone": "string or null",
    "primary_cta": "string or null",
    "secondary_cta": "string or null",
    "seo_angle": "string or null"
  },
  "brand_identity": {
    "existing_logo": false,
    "brand_colors": ["#RRGGBB"],
    "style_keywords": ["string"],
    "typography_hints": ["string"]
  },
  "pages": [
    {
      "name": "string",
      "url": "string or null",
      "priority": 1,
      "seo": {"title": "string or null", "meta_description": "string or null"},
      "sections": [
        {"type": "string", "title": "string or null", "description": "string or null"}
      ],
      "content": "verbatim marketing copy for this page, or null"
    }
  ],
  "seo": {
    "keywords": ["string"],
    "languages": ["fr"]
  },
  "technical_requirements": {
    "needs_cms": false,
    "integrations": ["string"],
    "responsive_required": true,
    "images_needed": ["string"],
    "social_links": {"facebook": "url", "instagram": "url"},
    "compliance": ["string"],
    "deliverables": ["string"]
  },
  "raw_summary": "1-2 sentence summary of the project"
}
"""


class CDCAnalyzerAgent:
    def __init__(self, llm: LLMTool | None = None):
        self.llm = llm or LLMTool()

    def _build_prompt(self, cdc_text: str, condensed: bool = False) -> str:
        text = cdc_text if not condensed else cdc_text[:4000]
        note = (
            "\n\nNote: the source text was truncated for length; extract what you can."
            if condensed
            else ""
        )
        return (
            f"Here is the client's CDC (project brief):\n"
            f"---\n{text}\n---{note}\n\n{JSON_SHAPE_HINT}"
        )

    def analyze(self, cdc_text: str) -> CDCAnalysis:
        if not cdc_text or not cdc_text.strip():
            raise ValueError("cdc_text is empty — nothing to analyze")

        full_prompt = self._build_prompt(cdc_text, condensed=False)
        retry_prompt = self._build_prompt(cdc_text, condensed=True)

        try:
            raw_json = self.llm.generate(
                prompt=full_prompt,
                system=SYSTEM_PROMPT,
                expect_json=True,
                temperature=0.3,
                retry_prompt=retry_prompt,
            )
        except LLMGenerationError as e:
            raise LLMGenerationError(f"CDC analysis failed: {e}") from e

        try:
            return CDCAnalysis.model_validate(raw_json)
        except ValidationError as e:
            raise LLMGenerationError(
                f"LLM JSON did not match CDCAnalysis schema: {e}"
            ) from e
