"""
app/agents/html_generator_agent.py

CORRECTIFS v2 :
- _slugify utilise unicodedata pour les accents (cohérence avec site_structure_agent).
- Les sections CTA (nom contenant "cta", "devis", "contact") recoivent un rendu
  distinct (bouton <a> visuellement marque) plutot qu'un simple <p>.
- La page Galerie recoit un layout grille CSS natif (grid) pour les photos.
- Google Fonts integre via <link> dans le <head> pour eviter les polices manquantes.
"""
import datetime
import logging
import re
import unicodedata
from pathlib import Path
from typing import List

from app.mcp.agents.sitegen.schemas import CDCData, DesignSystem, Route, Section, SiteStructure

logger = logging.getLogger(__name__)


def _slugify(name: str) -> str:
    slug = unicodedata.normalize("NFD", name or "")
    slug = "".join(c for c in slug if unicodedata.category(c) != "Mn")
    slug = slug.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "page"


def _escape(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _is_cta_section(name: str) -> bool:
    keywords = {"cta", "devis", "contact", "appel", "action"}
    return any(k in name.lower() for k in keywords)


def _build_nav_links(routes: List[Route], from_subdir: bool) -> str:
    links = []
    for route in routes:
        label = route.page.replace("-", " ").title()
        if route.url == "/":
            href = "../index.html" if from_subdir else "index.html"
        else:
            slug = _slugify(route.page)
            href = f"{slug}.html" if from_subdir else f"pages/{slug}.html"
        links.append(f'<a href="{href}">{_escape(label)}</a>')
    return "\n      ".join(links)


def _build_sections_html(sections: List[Section], page_key: str = "") -> str:
    if not sections:
        return "    <section>\n      <p>Contenu a venir.</p>\n    </section>"

    blocks = []
    is_gallery = "galeri" in page_key.lower()

    for section in sections:
        title = _escape((section.name or "").strip())
        body = _escape((section.content or "").strip())
        is_cta = _is_cta_section(section.name or "")

        block_lines = ['    <section class="cta-section">' if is_cta else "    <section>"]

        if title:
            tag = "h2"
            block_lines.append(f"      <{tag}>{title}</{tag}>")

        if is_cta:
            cta_label = "Demander un devis personnalise"
            block_lines.append(
                f'      <a href="pages/contact.html" class="btn-cta">{cta_label}</a>'
            )
        elif is_gallery and body:
            # Rendu galerie : liste de photos simulees
            block_lines.append('      <div class="gallery-grid">')
            block_lines.append(f"        <p>{body}</p>")
            block_lines.append("      </div>")
        elif body:
            block_lines.append(f"      <p>{body}</p>")
        elif not title:
            block_lines.append("      <p>Contenu a venir.</p>")

        block_lines.append("    </section>")
        blocks.append("\n".join(block_lines))

    return "\n".join(blocks)


def _google_fonts_link(font: str) -> str:
    """Genere un <link> Google Fonts pour la police principale."""
    font_url = font.replace(" ", "+")
    return (
        f'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        f'  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        f'  <link href="https://fonts.googleapis.com/css2?family={font_url}:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">'
    )


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  {fonts_link}
  <link rel="stylesheet" href="{css_path}">
</head>
<body>
  <header>
    <div class="header-inner">
      <span class="site-title">{company_name}</span>
      <nav>
        {nav_links}
      </nav>
    </div>
  </header>

  <main>
{sections}
  </main>

  <footer>
    <p>&copy; {year} {company_name}. Tous droits reserves.</p>
  </footer>
</body>
</html>
"""


CSS_TEMPLATE = """:root {{
  --color-primary:    {primary};
  --color-secondary:  {secondary};
  --color-background: {background};
  --font-main:        '{font_main}', Georgia, serif;
  --spacing-base:     {spacing_base};
  --radius-small:     {radius_small};
  --radius-medium:    {radius_medium};
}}

*, *::before, *::after {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  font-family: var(--font-main);
  background-color: var(--color-background);
  color: #2d2d2d;
  line-height: 1.7;
}}

/* ---- HEADER ---- */
header {{
  background-color: var(--color-primary);
  padding: calc(var(--spacing-base) * 2) calc(var(--spacing-base) * 3);
}}

.header-inner {{
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: calc(var(--spacing-base) * 1);
}}

.site-title {{
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-secondary);
  letter-spacing: 0.05em;
}}

header nav a {{
  color: var(--color-secondary);
  text-decoration: none;
  margin-left: calc(var(--spacing-base) * 2.5);
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  transition: opacity 0.2s;
}}

header nav a:hover {{
  opacity: 0.7;
  text-decoration: underline;
}}

/* ---- MAIN ---- */
main {{
  max-width: 960px;
  margin: 0 auto;
  padding: calc(var(--spacing-base) * 5) calc(var(--spacing-base) * 2);
}}

/* ---- SECTIONS ---- */
section {{
  margin-bottom: calc(var(--spacing-base) * 5);
  padding: calc(var(--spacing-base) * 4);
  background-color: #fff;
  border-radius: var(--radius-medium);
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}

section h1 {{
  color: var(--color-secondary);
  font-size: 2rem;
  margin-top: 0;
}}

section h2 {{
  color: var(--color-secondary);
  font-size: 1.35rem;
  margin-top: 0;
  border-bottom: 2px solid var(--color-primary);
  padding-bottom: calc(var(--spacing-base) * 1);
}}

section p {{
  max-width: 700px;
}}

/* ---- CTA ---- */
.cta-section {{
  background-color: var(--color-primary);
  text-align: center;
}}

.cta-section h2 {{
  color: var(--color-secondary);
  border-bottom: none;
}}

.btn-cta {{
  display: inline-block;
  margin-top: calc(var(--spacing-base) * 2);
  padding: calc(var(--spacing-base) * 1.5) calc(var(--spacing-base) * 4);
  background-color: var(--color-secondary);
  color: #fff;
  text-decoration: none;
  border-radius: var(--radius-small);
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: 0.04em;
  transition: opacity 0.2s;
}}

.btn-cta:hover {{
  opacity: 0.85;
}}

/* ---- GALLERY GRID ---- */
.gallery-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: calc(var(--spacing-base) * 2);
}}

/* ---- FOOTER ---- */
footer {{
  background-color: var(--color-secondary);
  color: #fff;
  text-align: center;
  padding: calc(var(--spacing-base) * 2.5);
  font-size: 0.9rem;
  letter-spacing: 0.03em;
}}

/* ---- RESPONSIVE ---- */
@media (max-width: 640px) {{
  .header-inner {{
    flex-direction: column;
    align-items: flex-start;
  }}
  header nav a {{
    margin-left: 0;
    margin-right: calc(var(--spacing-base) * 1.5);
  }}
  section {{
    padding: calc(var(--spacing-base) * 2.5);
  }}
}}
"""


def _write_css(design: DesignSystem, css_path: Path) -> None:
    css = CSS_TEMPLATE.format(
        primary=design.colors.primary,
        secondary=design.colors.secondary,
        background=design.colors.background,
        font_main=design.fonts.main,
        spacing_base=design.spacing.base,
        radius_small=design.radius.small,
        radius_medium=design.radius.medium,
    )
    css_path.write_text(css, encoding="utf-8")


def generate_site(
    cdc: CDCData,
    design: DesignSystem,
    structure: SiteStructure,
    output_dir: str,
) -> str:
    site_dir  = Path(output_dir) / "generated_site"
    pages_dir = site_dir / "pages"
    assets_dir = site_dir / "assets"
    pages_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    _write_css(design, assets_dir / "style.css")

    company_name = cdc.company.name.strip() or "Mon Entreprise"
    description = ""
    if isinstance(cdc.seo, dict):
        description = (
            cdc.seo.get("description") or cdc.seo.get("meta_description") or ""
        ).strip()
    if not description:
        description = cdc.company.activity.strip()

    year   = datetime.datetime.now().year
    routes = structure.routes or [Route(page="home", url="/", sections=[])]
    fonts_link = _google_fonts_link(design.fonts.main)

    for route in routes:
        is_home    = route.url == "/"
        from_sub   = not is_home
        nav_links  = _build_nav_links(routes, from_subdir=from_sub)
        secs_html  = _build_sections_html(route.sections, page_key=route.page)
        css_path   = "assets/style.css" if is_home else "../assets/style.css"
        page_title = (
            company_name
            if is_home
            else f"{company_name} — {route.page.replace('-', ' ').title()}"
        )

        html = PAGE_TEMPLATE.format(
            title=_escape(page_title),
            description=_escape(description),
            fonts_link=fonts_link,
            css_path=css_path,
            nav_links=nav_links,
            sections=secs_html,
            year=year,
            company_name=_escape(company_name),
        )

        if is_home:
            (site_dir / "index.html").write_text(html, encoding="utf-8")
        else:
            slug = _slugify(route.page)
            (pages_dir / f"{slug}.html").write_text(html, encoding="utf-8")

    logger.info("[HTMLGenerator] Site genere dans %s (%d pages)", site_dir, len(routes))
    return str(site_dir)
