# app/mcp/agents/design_generator_agent.py
import json
import re
from app.llm.llm_tool import LLMTool
from app.services.design_schema import (
    DesignJSON, Branding, ColorToken, TypographyToken,
    FontWeight, Page, Section, ComponentType
)


class DesignGeneratorAgent:
    def __init__(self):
        self.llm = LLMTool()

    def run(self, client_data: dict) -> DesignJSON:
        """Point d'entrée. Reçoit le dict de adapt_for_design()."""
        prompt = self._build_prompt(client_data)

        # ← .generate() avec expect_json=True pour nettoyage auto
        raw = self.llm.generate(prompt, expect_json=True)

        return self._parse_and_validate(raw, client_data)

    def _build_prompt(self, d: dict) -> str:
        services_str = ", ".join(d.get("services", [])[:5]) or "Non précisé"
        pages_str    = ", ".join(d.get("pages", ["Accueil", "Services", "Contact"]))
        keywords_str = ", ".join(str(k) for k in d.get("keywords", [])[:8]) or "Non précisé"

        # System + user fusionnés en un seul prompt (interface LLMTool)
        return f"""Tu es un expert en design web.
À partir des données client ci-dessous, génère un DESIGN JSON structuré.

RÈGLES ABSOLUES :
- Réponds UNIQUEMENT avec du JSON valide, rien d'autre
- Aucun texte avant ou après le JSON
- Chaque couleur hex doit être valide (#RRGGBB)
- Maximum 6 pages, maximum 8 sections par page
- Types de sections valides : hero, navbar, card_grid, testimonials, cta, footer, contact_form, gallery, faq, team
- Contenus concrets et spécifiques au client, pas de placeholders

DONNÉES CLIENT :
- Nom       : {d.get('name', 'N/A')}
- Secteur   : {d.get('sector', 'N/A')}
- Ville     : {d.get('city', 'N/A')}
- Activité  : {d.get('description', 'N/A')}
- Services  : {services_str}
- Pages     : {pages_str}
- Couleurs  : {d.get('colors', [])}
- Mots-clés : {keywords_str}

SCHÉMA JSON ATTENDU (respecte exactement cette structure) :
{{
  "version": "1.0",
  "client_id": "{d.get('id', 'unknown')}",
  "client_name": "{d.get('name', 'Client')}",
  "branding": {{
    "colors": [
      {{"hex": "#RRGGBB", "role": "primary", "name": "Nom couleur"}},
      {{"hex": "#RRGGBB", "role": "secondary", "name": "Nom couleur"}},
      {{"hex": "#RRGGBB", "role": "accent", "name": "Nom couleur"}},
      {{"hex": "#FFFFFF", "role": "background", "name": "Fond"}},
      {{"hex": "#333333", "role": "text", "name": "Texte"}}
    ],
    "typography": [
      {{"family": "Inter", "weight": "700", "size_desktop": 48, "size_mobile": 32, "role": "heading1"}},
      {{"family": "Inter", "weight": "400", "size_desktop": 16, "size_mobile": 14, "role": "body"}}
    ],
    "border_radius": 8
  }},
  "pages": [
    {{
      "id": "home",
      "title": "Accueil",
      "slug": "/",
      "is_priority": true,
      "sections": [
        {{"id": "navbar_1", "type": "navbar", "order": 0}},
        {{"id": "hero_1", "type": "hero", "order": 1, "headline": "Titre accrocheur", "subheadline": "Description courte", "cta_text": "Découvrir"}},
        {{"id": "card_grid_1", "type": "card_grid", "order": 2, "headline": "Nos services", "content_hints": ["Service 1", "Service 2", "Service 3"]}},
        {{"id": "cta_1", "type": "cta", "order": 3, "headline": "Prêt à commencer ?", "cta_text": "Nous contacter"}},
        {{"id": "footer_1", "type": "footer", "order": 99}}
      ]
    }}
  ],
  "global_notes": []
}}

Génère maintenant le JSON complet pour ce client. Commence directement par {{"""

    def _parse_and_validate(self, raw: str, fallback: dict) -> DesignJSON:
        # LLMTool._clean_json_response() a déjà nettoyé, mais on remet
        # le "{" qu'on a demandé au LLM de commencer par là
        if raw and not raw.startswith("{"):
            match = re.search(r"\{.*", raw, re.DOTALL)
            raw = match.group() if match else raw

        try:
            data = json.loads(raw)
            return DesignJSON(**data)
        except Exception as e:
            print(f"[DesignGeneratorAgent] Parsing échoué ({e}), fallback utilisé.")
            print(f"[DesignGeneratorAgent] Raw reçu : {raw[:300]}")
            return self._minimal_fallback(fallback)

    def _minimal_fallback(self, d: dict) -> DesignJSON:
        return DesignJSON(
            client_id=d.get("id", "unknown"),
            client_name=d.get("name", "Client"),
            branding=Branding(
                colors=[
                    ColorToken(hex="#1A1A2E", role="primary",    name="Principal"),
                    ColorToken(hex="#16213E", role="secondary",   name="Secondaire"),
                    ColorToken(hex="#E94560", role="accent",      name="Accent"),
                    ColorToken(hex="#FFFFFF", role="background",  name="Fond"),
                    ColorToken(hex="#333333", role="text",        name="Texte"),
                ],
                typography=[
                    TypographyToken(family="Inter", weight=FontWeight.BOLD,
                                    size_desktop=48, size_mobile=32, role="heading1"),
                    TypographyToken(family="Inter", weight=FontWeight.REGULAR,
                                    size_desktop=16, size_mobile=14, role="body"),
                ]
            ),
            pages=[
                Page(
                    id="home", title="Accueil", slug="/", is_priority=True,
                    sections=[
                        Section(id="navbar_1", type=ComponentType.NAVBAR, order=0),
                        Section(id="hero_1",   type=ComponentType.HERO,   order=1,
                                headline=f"Bienvenue chez {d.get('name', 'nous')}",
                                subheadline="Votre partenaire de confiance",
                                cta_text="Découvrir nos services"),
                        Section(id="cta_1",    type=ComponentType.CTA,    order=2,
                                headline="Contactez-nous", cta_text="Prendre contact"),
                        Section(id="footer_1", type=ComponentType.FOOTER, order=99),
                    ]
                )
            ]
        )