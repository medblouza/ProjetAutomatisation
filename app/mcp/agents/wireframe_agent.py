"""
app/agents/wireframe_agent.py
Génère un wireframe HTML à partir des données nettoyées.
Groq (llama-3.3-70b-versatile) avec tool calls, un appel par page.
Pas de Figma — le wireframe est un fichier HTML autonome.
"""

import json
import os
from typing import Optional
from groq import Groq

# ──────────────────────────────────────────────
# Tools Groq
# ──────────────────────────────────────────────

TOOL_CREATE_PAGE = {
    "type": "function",
    "function": {
        "name": "create_page_structure",
        "description": "Crée la structure d'UNE SEULE page. Appelle cette fonction une seule fois par message.",
        "parameters": {
            "type": "object",
            "properties": {
                "page_name": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name":        {"type": "string"},
                            "type":        {"type": "string", "enum": ["navbar", "hero", "text", "grid", "gallery", "cta", "form", "footer"]},
                            "height":      {"type": "integer"},
                            "description": {"type": "string"},
                        },
                        "required": ["name", "type"],
                    },
                },
            },
            "required": ["page_name", "sections"],
        },
    },
}

TOOL_FINALIZE = {
    "type": "function",
    "function": {
        "name": "finalize_wireframe",
        "description": "Finalise le wireframe. Appelle UNE SEULE FOIS après toutes les pages.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "global_style": {
                    "type": "object",
                    "properties": {
                        "primary_color":   {"type": "string"},
                        "secondary_color": {"type": "string"},
                        "style":           {"type": "string"},
                    },
                },
            },
            "required": ["project_name"],
        },
    },
}


# ──────────────────────────────────────────────
# Agent
# ──────────────────────────────────────────────

class WireframeAgent:
    MODEL = "llama-3.3-70b-versatile"

    def __init__(self, team_id: Optional[str] = None):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
        self._pages: list[dict] = []
        self._style: dict = {}

    def run(self, cleaned_data: dict) -> dict:
        """
        Retourne :
        {
            "html": "<html>...</html>",   ← wireframe complet
            "pages": [...],
            "style": {...},
            "project_name": "...",
            "pages_count": N,
        }
        """
        pages_from_dp = cleaned_data.get("pages", [])
        if not pages_from_dp:
            raise RuntimeError("Aucune page trouvée dans les données nettoyées.")

        system_prompt = self._build_system_prompt()

        # 1 requête LLM par page
        for page in pages_from_dp:
            self._process_one_page(system_prompt, page, cleaned_data)

        # Récupère le style via finalize
        style_args = self._get_style(system_prompt, cleaned_data)
        self._style = style_args.get("global_style", {})
        project_name = style_args.get("project_name", cleaned_data.get("company_name", "Wireframe"))

        # Génère le HTML côté Python (pas besoin du LLM pour ça)
        html = self._generate_html(project_name, cleaned_data)

        return {
            "html": html,
            "pages": self._pages,
            "style": self._style,
            "project_name": project_name,
            "pages_count": len(self._pages),
        }

    # ── Une page ─────────────────────────────────────────────

    def _process_one_page(self, system_prompt: str, page: dict, cleaned_data: dict):
        branding    = cleaned_data.get("branding", {})
        style_names = ", ".join(s.get("name", "") for s in branding.get("style", [])) or "Moderne"
        colors      = branding.get("colors", [])

        user_prompt = f"""Crée la structure pour cette page. Appelle create_page_structure UNE SEULE FOIS.

Page : {page['name']}
Contenu : {page.get('content', '')[:400]}

Activité : {cleaned_data.get('activity', '')}
Style    : {style_names}
Couleur  : {colors[0] if colors else '#000'}

RAPPEL : navbar en premier, footer en dernier."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

        for _ in range(5):
            resp = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                tools=[TOOL_CREATE_PAGE],
                tool_choice={"type": "function", "function": {"name": "create_page_structure"}},
                max_tokens=1024,
            )
            msg = resp.choices[0].message
            messages.append(msg.model_dump())

            if msg.tool_calls:
                tc     = msg.tool_calls[0]
                args   = json.loads(tc.function.arguments)
                result = self._tool_create_page(args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
                break

    # ── Finalisation (style uniquement) ──────────────────────

    def _get_style(self, system_prompt: str, cleaned_data: dict) -> dict:
        branding    = cleaned_data.get("branding", {})
        colors      = branding.get("colors", [])
        style_names = ", ".join(s.get("name", "") for s in branding.get("style", [])) or "Moderne"
        pages_done  = ", ".join(p["name"] for p in self._pages)

        user_prompt = f"""Pages créées : {pages_done}.
Appelle finalize_wireframe pour le projet "{cleaned_data.get('company_name', 'Client')}".
Style : {style_names} | Couleur 1 : {colors[0] if colors else '#000'} | Couleur 2 : {colors[1] if len(colors) > 1 else '#fff'}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

        for _ in range(5):
            resp = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                tools=[TOOL_FINALIZE],
                tool_choice={"type": "function", "function": {"name": "finalize_wireframe"}},
                max_tokens=256,
            )
            msg = resp.choices[0].message
            messages.append(msg.model_dump())

            if msg.tool_calls:
                return json.loads(msg.tool_calls[0].function.arguments)

        # Fallback si Groq ne répond pas
        return {
            "project_name": cleaned_data.get("company_name", "Wireframe"),
            "global_style": {
                "primary_color":   colors[0] if colors else "#333333",
                "secondary_color": colors[1] if len(colors) > 1 else "#ffffff",
                "style":           style_names,
            },
        }

    # ── Tool handler ──────────────────────────────────────────

    def _tool_create_page(self, args: dict) -> dict:
        self._pages.append({
            "name":     args["page_name"],
            "sections": args.get("sections", []),
        })
        return {"status": "ok", "page_added": args["page_name"], "total_pages": len(self._pages)}

    # ── System prompt ─────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        return """Tu es un expert UX/UI designer. Tu crées des wireframes pour des sites web professionnels.

RÈGLES :
- create_page_structure : UNE SEULE FOIS par message, pour UNE SEULE page.
- Chaque page : "navbar" en premier, "footer" en dernier.
- Jamais plusieurs fonctions dans le même message.

CONTENU → TYPE :
- Galerie photos              → gallery
- Formulaire / contact / devis → form
- Présentation / texte         → text
- Services / grille de cartes  → grid
- Bannière / accroche          → hero
- Appel à l'action             → cta
- Adresse / carte              → form

TYPES : navbar · hero · text · grid · gallery · cta · form · footer"""

    # ── Générateur HTML ───────────────────────────────────────

    def _generate_html(self, project_name: str, cleaned_data: dict) -> str:
        branding        = cleaned_data.get("branding", {})
        colors          = branding.get("colors", [])
        styles          = branding.get("style", [])
        primary         = colors[0] if colors else "#333333"
        secondary       = colors[1] if len(colors) > 1 else "#f5f5f5"
        style_label     = ", ".join(s.get("name", "") for s in styles) or "Moderne"
        company         = cleaned_data.get("company_name", project_name)
        activity        = cleaned_data.get("activity", "")

        # Couleur de texte adaptée au fond
        def text_color(hex_color: str) -> str:
            hex_color = hex_color.lstrip("#")
            if len(hex_color) == 3:
                hex_color = "".join(c*2 for c in hex_color)
            try:
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                luminance = (0.299*r + 0.587*g + 0.114*b) / 255
                return "#111111" if luminance > 0.5 else "#ffffff"
            except Exception:
                return "#111111"

        primary_text = text_color(primary)

        # Hauteurs et couleurs par type de section
        section_config = {
            "navbar":  {"height": "70px",  "bg": primary,    "label_color": primary_text,  "opacity": "1"},
            "hero":    {"height": "380px", "bg": "#e8e8e8",  "label_color": "#333",         "opacity": "1"},
            "text":    {"height": "200px", "bg": "#f9f9f9",  "label_color": "#444",         "opacity": "1"},
            "grid":    {"height": "280px", "bg": "#f0f0f0",  "label_color": "#444",         "opacity": "1"},
            "gallery": {"height": "300px", "bg": "#ebebeb",  "label_color": "#444",         "opacity": "1"},
            "cta":     {"height": "160px", "bg": secondary,  "label_color": text_color(secondary), "opacity": "1"},
            "form":    {"height": "260px", "bg": "#fafafa",  "label_color": "#444",         "opacity": "1"},
            "footer":  {"height": "140px", "bg": "#2c2c2c",  "label_color": "#ffffff",      "opacity": "1"},
        }

        # Icônes ASCII par type
        section_icons = {
            "navbar": "☰", "hero": "▬", "text": "≡",
            "grid": "⊞", "gallery": "⊟", "cta": "▶",
            "form": "✉", "footer": "◼",
        }

        # Construction des onglets (pages) et leur contenu HTML
        tabs_html    = ""
        content_html = ""

        for i, page in enumerate(self._pages):
            active_tab     = "active" if i == 0 else ""
            active_content = "active" if i == 0 else ""
            page_id        = f"page_{i}"

            tabs_html += f'<button class="tab-btn {active_tab}" onclick="showPage(\'{page_id}\')">{page["name"]}</button>\n'

            sections_html = ""
            for section in page.get("sections", []):
                stype  = section.get("type", "text")
                sname  = section.get("name", stype)
                sdesc  = section.get("description", "")
                cfg    = section_config.get(stype, section_config["text"])
                icon   = section_icons.get(stype, "□")
                height = f"{section['height']}px" if section.get("height") else cfg["height"]

                inner = self._section_inner_html(stype, sname, sdesc, company, primary, primary_text)

                sections_html += f"""
<div class="section section-{stype}" style="height:{height};background:{cfg['bg']};">
  <div class="section-label" style="color:{cfg['label_color']}">{icon} {sname}</div>
  <div class="section-inner">{inner}</div>
  <div class="section-type-badge">{stype}</div>
</div>"""

            content_html += f"""
<div id="{page_id}" class="page-content {active_content}">
  {sections_html}
</div>"""

        pages_list_html = "".join(
            f"<li>{p['name']} — {len(p.get('sections', []))} sections</li>"
            for p in self._pages
        )

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wireframe — {company}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f4f4f4; }}

  /* ── Header ── */
  .wf-header {{
    background: {primary};
    color: {primary_text};
    padding: 18px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0,0,0,.15);
  }}
  .wf-header h1 {{ font-size: 20px; font-weight: 600; letter-spacing: .3px; }}
  .wf-meta {{ font-size: 12px; opacity: .8; }}

  /* ── Tabs ── */
  .tabs-bar {{
    background: #fff;
    border-bottom: 2px solid #e0e0e0;
    padding: 0 32px;
    display: flex;
    gap: 4px;
    overflow-x: auto;
  }}
  .tab-btn {{
    background: none;
    border: none;
    padding: 14px 20px;
    font-size: 14px;
    cursor: pointer;
    color: #666;
    border-bottom: 3px solid transparent;
    white-space: nowrap;
    transition: all .2s;
  }}
  .tab-btn:hover  {{ color: {primary}; }}
  .tab-btn.active {{ color: {primary}; border-bottom-color: {primary}; font-weight: 600; }}

  /* ── Layout ── */
  .wf-body {{
    display: flex;
    gap: 0;
    min-height: calc(100vh - 120px);
  }}
  .wf-canvas {{
    flex: 1;
    padding: 24px;
    overflow-y: auto;
  }}
  .wf-sidebar {{
    width: 220px;
    background: #fff;
    border-left: 1px solid #e0e0e0;
    padding: 20px 16px;
    font-size: 13px;
    color: #555;
  }}
  .wf-sidebar h3 {{ font-size: 12px; text-transform: uppercase; letter-spacing: .8px; color: #999; margin-bottom: 12px; }}
  .wf-sidebar ul {{ list-style: none; }}
  .wf-sidebar li {{ padding: 6px 0; border-bottom: 1px solid #f0f0f0; }}

  /* ── Page content ── */
  .page-content {{ display: none; max-width: 960px; margin: 0 auto; }}
  .page-content.active {{ display: block; }}

  /* ── Sections ── */
  .section {{
    position: relative;
    width: 100%;
    margin-bottom: 4px;
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border: 1px solid rgba(0,0,0,.07);
  }}
  .section-label {{
    position: absolute;
    top: 10px;
    left: 14px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .6px;
    opacity: .7;
  }}
  .section-type-badge {{
    position: absolute;
    top: 10px;
    right: 14px;
    font-size: 10px;
    background: rgba(0,0,0,.08);
    color: inherit;
    padding: 2px 8px;
    border-radius: 10px;
    opacity: .6;
  }}
  .section-inner {{
    padding: 36px 24px 16px;
    width: 100%;
  }}

  /* ── Section inners ── */
  .placeholder-box {{
    background: rgba(0,0,0,.06);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(0,0,0,.35);
    font-size: 13px;
  }}
  .placeholder-line {{
    height: 12px;
    background: rgba(0,0,0,.1);
    border-radius: 6px;
    margin-bottom: 8px;
  }}
  .grid-mock {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .grid-card {{
    background: rgba(255,255,255,.7);
    border-radius: 6px;
    padding: 16px;
    text-align: center;
    border: 1px solid rgba(0,0,0,.08);
  }}
  .grid-card-icon {{ font-size: 24px; margin-bottom: 8px; }}
  .gallery-mock {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }}
  .gallery-photo {{ background: rgba(0,0,0,.12); border-radius: 4px; aspect-ratio: 1; }}
  .form-mock {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
  .form-field {{
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 4px;
    height: 38px;
  }}
  .form-field.full {{ grid-column: span 2; }}
  .form-field.textarea {{ height: 80px; grid-column: span 2; }}
  .form-btn {{
    grid-column: span 2;
    background: {primary};
    color: {primary_text};
    border: none;
    border-radius: 4px;
    height: 42px;
    font-size: 14px;
    cursor: pointer;
  }}
  .hero-mock {{ text-align: center; padding: 40px 0; }}
  .hero-title {{
    font-size: 28px;
    font-weight: 700;
    color: #333;
    margin-bottom: 12px;
  }}
  .hero-sub {{ font-size: 15px; color: #666; margin-bottom: 20px; }}
  .hero-btn {{
    display: inline-block;
    background: {primary};
    color: {primary_text};
    padding: 12px 28px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 600;
  }}
  .navbar-mock {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 12px;
  }}
  .nav-logo {{ font-weight: 700; font-size: 16px; }}
  .nav-links {{ display: flex; gap: 20px; font-size: 13px; opacity: .8; }}
  .footer-mock {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    color: #ccc;
    font-size: 12px;
  }}
  .footer-col-title {{ color: #fff; font-weight: 600; margin-bottom: 8px; font-size: 13px; }}
  .cta-mock {{ text-align: center; }}
  .cta-text {{ font-size: 18px; font-weight: 600; margin-bottom: 12px; color: #333; }}
  .cta-btn {{
    display: inline-block;
    background: {primary};
    color: {primary_text};
    padding: 10px 24px;
    border-radius: 4px;
    font-size: 14px;
  }}
</style>
</head>
<body>

<div class="wf-header">
  <h1>📐 {company}</h1>
  <span class="wf-meta">{activity} · Style : {style_label} · {len(self._pages)} pages</span>
</div>

<div class="tabs-bar">
  {tabs_html}
</div>

<div class="wf-body">
  <div class="wf-canvas">
    {content_html}
  </div>
  <div class="wf-sidebar">
    <h3>Pages ({len(self._pages)})</h3>
    <ul>{pages_list_html}</ul>
    <br>
    <h3>Branding</h3>
    <div style="display:flex;gap:6px;margin-bottom:8px">
      <div style="width:28px;height:28px;border-radius:4px;background:{primary};border:1px solid #ccc" title="{primary}"></div>
      <div style="width:28px;height:28px;border-radius:4px;background:{secondary};border:1px solid #ccc" title="{secondary}"></div>
    </div>
    <div style="font-size:12px;color:#888">{style_label}</div>
  </div>
</div>

<script>
function showPage(id) {{
  document.querySelectorAll('.page-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
}}
</script>
</body>
</html>"""

    def _section_inner_html(self, stype: str, name: str, desc: str, company: str, primary: str, primary_text: str) -> str:
        pages_names = [p["name"] for p in self._pages] or ["Accueil", "Services", "Contact"]

        if stype == "navbar":
            links = "  ".join(f'<span>{p}</span>' for p in pages_names[:5])
            return f'<div class="navbar-mock"><span class="nav-logo">{company}</span><div class="nav-links">{links}</div></div>'

        if stype == "hero":
            return f'''<div class="hero-mock">
  <div class="hero-title">{company}</div>
  <div class="hero-sub">{desc or "Bienvenue sur notre site"}</div>
  <span class="hero-btn">Nous contacter</span>
</div>'''

        if stype == "text":
            return '''<div>
  <div class="placeholder-line" style="width:60%"></div>
  <div class="placeholder-line" style="width:90%"></div>
  <div class="placeholder-line" style="width:75%"></div>
  <div class="placeholder-line" style="width:85%"></div>
  <div class="placeholder-line" style="width:50%"></div>
</div>'''

        if stype == "grid":
            cards = "".join(f'<div class="grid-card"><div class="grid-card-icon">◼</div><div class="placeholder-line"></div><div class="placeholder-line" style="width:70%"></div></div>' for _ in range(3))
            return f'<div class="grid-mock">{cards}</div>'

        if stype == "gallery":
            photos = "".join('<div class="gallery-photo"></div>' for _ in range(8))
            return f'<div class="gallery-mock">{photos}</div>'

        if stype == "cta":
            return f'''<div class="cta-mock">
  <div class="cta-text">{desc or "Contactez-nous dès maintenant"}</div>
  <span class="cta-btn">Demander un devis</span>
</div>'''

        if stype == "form":
            return '''<div class="form-mock">
  <div class="form-field"></div>
  <div class="form-field"></div>
  <div class="form-field full"></div>
  <div class="form-field textarea"></div>
  <button class="form-btn">Envoyer</button>
</div>'''

        if stype == "footer":
            return f'''<div class="footer-mock">
  <div><div class="footer-col-title">{company}</div><div class="placeholder-line" style="width:80%"></div><div class="placeholder-line" style="width:60%"></div></div>
  <div><div class="footer-col-title">Navigation</div>{"".join(f'<div class="placeholder-line" style="width:55%"></div>' for _ in range(3))}</div>
  <div><div class="footer-col-title">Contact</div>{"".join(f'<div class="placeholder-line" style="width:70%"></div>' for _ in range(3))}</div>
</div>'''

        return f'<div class="placeholder-box" style="height:80px">{name}</div>'