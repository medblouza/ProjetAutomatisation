from __future__ import annotations

from pydantic import ValidationError

from app.schema.cdc_schema import PageSpec
from app.schema.design_schema import ComponentInstance
from app.services.llm_service import LLMTool, LLMGenerationError

ALLOWED_TYPES = [
    "navbar", "hero", "features", "services_grid", "gallery", "testimonials",
    "faq", "pricing", "cta", "map", "contact_form", "footer", "image_banner",
    "cards", "statistics", "timeline", "logo_cloud",
]

SYSTEM_PROMPT = f"""Senior UX/UI Architect. Convert one page into UI components.
Output ONLY a JSON array, no markdown, no explanation.

Allowed types: {ALLOWED_TYPES}
Rules:
- Never invent a type. Page starts with navbar, ends with footer.
- Populate every field with real content from the CDC; never leave empty if data exists.
- Multiple services/features/testimonials/prices/FAQ/images -> multiple items.
- Copy client wording exactly, don't summarize.
- Use variants: hero=split, features=3-columns, gallery=masonry, cards=icon-top, statistics=horizontal.
- assets[] items MUST be: {{"type","description","alt_text","placeholder_url"}} — never other keys.
- Preserve section order.
"""

def _normalize_asset(raw: dict) -> dict:
    """
    Makes the LLM's asset dict tolerant to schema drift we've observed:
    the LLM sometimes emits {"url": "...", "alt": "..."} instead of the
    Asset shape {"type", "description", "alt_text", "placeholder_url"}.
    Never mutates the input dict.
    """
    normalized = dict(raw)

    # url -> placeholder_url
    if "placeholder_url" not in normalized and "url" in normalized:
        normalized["placeholder_url"] = normalized.pop("url")

    # alt -> alt_text
    if "alt_text" not in normalized and "alt" in normalized:
        normalized["alt_text"] = normalized.pop("alt")

    # required fields with sane fallbacks so validation never crashes on this
    normalized.setdefault("type", "image")
    normalized.setdefault(
        "description",
        normalized.get("alt_text") or "Image asset",
    )

    return normalized


def _normalize_component_assets(raw_component: dict) -> dict:
    """Normalizes raw_component['assets'] in place (on a dict) before
    Pydantic validation. Leaves the component untouched if 'assets' is
    missing or not a list."""
    if isinstance(raw_component.get("assets"), list):
        raw_component["assets"] = [
            _normalize_asset(a) if isinstance(a, dict) else a
            for a in raw_component["assets"]
        ]
    return raw_component


class ComponentPlannerAgent:
    def __init__(self, llm: LLMTool | None = None):
        self.llm = llm or LLMTool()

    def _build_prompt(self, page: PageSpec) -> str:
        sections_desc = "\n".join(
            f"- {s.type}" + (f": {s.description}" if s.description else "")
            for s in page.sections
        )
        return (
            f"Page name:\n{page.name}\n\n"

            f"Requested sections:\n"
            f"{sections_desc}\n\n"

            f"Marketing copy:\n"
            f"{page.content}\n\n"

            "Generate a JSON array of UI components.\n\n"

            "Each component must follow this schema:\n\n"

            "{\n"
            ' "id":"hero-01",\n'
            ' "type":"hero",\n'
            ' "variant":"split",\n'
            ' "order":1,\n'

            ' "content":{\n'
            '     "title":"",\n'
            '     "subtitle":"",\n'
            '     "body":"",\n'
            '     "cta_label":"",\n'
            '     "cta_url":"",\n'
            '     "items":[\n'
            '         {\n'
            '             "title":"",\n'
            '             "text":""\n'
            '         }\n'
            '     ]\n'
            ' },\n'

            ' "style":{\n'
            '     "alignment":"center",\n'
            '     "padding":"xl",\n'
            '     "background":"surface"\n'
            ' },\n'

            ' "assets":[\n'
            '     {\n'
            '         "type":"image",\n'
            '         "description":"",\n'
            '         "alt_text":"",\n'
            '         "placeholder_url":""\n'
            '     }\n'
            ' ]\n'

            "}\n\n"

            "Populate ALL applicable fields.\n"

            "Do NOT leave fields empty.\n"

            "If multiple services exist, create multiple items.\n"

            "If multiple features exist, create multiple items.\n"

            "If multiple testimonials exist, create multiple items.\n"

            "If a CTA exists anywhere, populate cta_label and cta_url.\n"

            "For any component with images, populate 'assets' using EXACTLY "
            "the shape shown above (type, description, alt_text, "
            "placeholder_url) — never any other keys.\n"

            "Copy the wording exactly.\n"
        )

    def plan(self, page: PageSpec) -> list[ComponentInstance]:
        prompt = self._build_prompt(page)
        try:
            raw = self.llm.generate(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                expect_json=True,
                temperature=0.1,
                expected_root="array",
            )
        except LLMGenerationError as e:
            raise LLMGenerationError(f"Component planning failed for page '{page.name}': {e}") from e

        if not isinstance(raw, list):
            raise LLMGenerationError(
                f"Expected a JSON array of components for page '{page.name}', got {type(raw)}"
            )

        raw = [
            _normalize_component_assets(item) if isinstance(item, dict) else item
            for item in raw
        ]

        try:
            return [ComponentInstance.model_validate(item) for item in raw]
        except ValidationError as e:
            raise LLMGenerationError(
                f"LLM produced an invalid component for page '{page.name}': {e}"
            ) from e