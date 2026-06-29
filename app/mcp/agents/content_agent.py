"""
Génère le cahier des charges complet : H1/H2, contenu SEO, recommandations design.
"""
import logging
import time
from app.llm.llm_tool import LLMTool
from app.utils.parsers import safe_string, safe_list

logger = logging.getLogger(__name__)


class ContentAgent:
    """
    Input  : dict (output de StructureAgent)
    Output : dict avec le CDC complet en string
    """

    def __init__(self, llm: LLMTool):
        self.llm = llm

    def run(self, structure_data: dict) -> dict:
        logger.info("[ContentAgent] Génération du cahier des charges...")

        sections = []

        # 1. En-tête du CDC
        sections.append(self._generate_header(structure_data))

        # 2. Brief créatif 
        sections.append(self._generate_brief_section(structure_data))


        # 3. Présentation client
        sections.append(self._generate_client_section(structure_data))

        # 4. Stratégie
        sections.append(self._generate_strategy_section(structure_data))

        # 5. Arborescence et contenu de chaque page
        sections.append(self._generate_pages_section(structure_data))

        # 6. Recommandations design
        sections.append(self._generate_design_section(structure_data))

        # 7. SEO
        sections.append(self._generate_seo_section(structure_data))

        # 8. Recommandations techniques
        sections.append(self._generate_technical_section(structure_data))

        cdc_content = "\n\n".join(filter(None, sections))
        logger.info(f"[ContentAgent] Sections générées : {len(sections)}")
        for i, s in enumerate(sections):
            logger.info(f"[ContentAgent] Section {i} — {len(s)} caractères")
        output = {
            **structure_data,
            "cdc_content": cdc_content,
        }

        logger.info(f"[ContentAgent] ✅ CDC généré — {len(cdc_content)} caractères")
        return output

    # ── Sections ──────────────────────────────────────────────────────────────

    def _generate_header(self, data: dict) -> str:
        company  = data.get("company_name", "")
        activity = data.get("activity", "")
        city     = data.get("city", "")
        return f"""# CAHIER DES CHARGES — CRÉATION DE SITE WEB
## {company}

**Activité :** {activity}
**Ville :** {city}
**Date de rédaction :** À compléter
**Version :** 1.0

---"""

    def _generate_client_section(self, data: dict) -> str:
        strategy = data.get("strategy", {})
        services = safe_list(data.get("services", []))
        diff     = safe_list(data.get("differentiators", []))

        services_md = "\n".join(f"- {s}" for s in services)
        diff_md     = "\n".join(f"- {d}" for d in diff)

        return f"""## 1. PRÉSENTATION DU CLIENT

**Entreprise :** {data.get('company_name', '')}
**Secteur d'activité :** {data.get('activity', '')}
**Localisation :** {data.get('city', '')}
**Zone d'intervention :** {data.get('zone', '')}
**Cible client :** {data.get('target', '')}

### Services proposés
{services_md if services_md else '- À compléter'}

### Points différenciants
{diff_md if diff_md else '- À compléter'}

### Expérience et histoire
{data.get('experience', 'Non renseigné')}

### Proposition de valeur unique
{strategy.get('unique_value', 'À définir')}"""

    def _generate_strategy_section(self, data: dict) -> str:
        strategy = data.get("strategy", {})
        obj      = safe_list(strategy.get("objectives", []))
        msgs     = safe_list(strategy.get("key_messages", []))

        obj_md  = "\n".join(f"- {o}" for o in obj)
        msgs_md = "\n".join(f"- {m}" for m in msgs)

        return f"""## 2. STRATÉGIE MARKETING DIGITALE

### Objectifs du site web
{obj_md if obj_md else '- À définir'}

### Messages clés à communiquer
{msgs_md if msgs_md else '- À définir'}

### Ton éditorial
{strategy.get('tone', 'Professionnel et accessible')}

### Appels à l'action
- **CTA Principal :** {strategy.get('cta_primary', 'Demander un devis')}
- **CTA Secondaire :** {strategy.get('cta_secondary', 'Découvrir nos services')}

### Angle SEO principal
{strategy.get('seo_angle', 'À définir')}"""

    def _generate_pages_section(self, data: dict) -> str:
        site_structure = data.get("site_structure", {})
        pages          = site_structure.get("pages", [])

        if not pages:
            return "## 3. ARBORESCENCE DU SITE\n\nÀ définir."

        pages_content = []
        pages_content.append("## 3. ARBORESCENCE ET CONTENU DES PAGES\n")
        pages_content.append(f"**Nombre de pages :** {len(pages)}\n")
        pages_content.append(f"**Navigation :** {' > '.join(p['name'] for p in pages)}\n")
        pages_content.append("---\n")

        for page in pages:
            sections = safe_list(page.get("sections", []))
            sections_md = "\n".join(f"  - {s}" for s in sections)

            page_block = f"""### Page : {page['name']}
**URL :** /{page.get('slug', '')}
**Priorité :** {page.get('priority', '')}
**Titre SEO :** {page.get('seo_title', '')}
**Meta description :** {page.get('meta_description', '')}

**Sections à intégrer :**
{sections_md if sections_md else '  - À définir'}

**Contenu LLM généré :**
{self._generate_page_content(page, data)}

---"""
            pages_content.append(page_block)

        return "\n".join(pages_content)

    def _generate_page_content(self, page: dict, data: dict) -> str:
        time.sleep(1)
        """Génère le contenu textuel d'une page via le LLM."""
        company  = data.get("company_name", "")
        activity = data.get("activity", "")
        city     = data.get("city", "")
        sections = safe_string(page.get("sections", []))
        strategy = data.get("strategy", {})

        prompt = f"""Tu es un rédacteur web SEO expert. Rédige le contenu de la page "{page['name']}" pour ce site web.

ENTREPRISE : {company} — {activity} à {city}
SECTIONS DE LA PAGE : {sections}
TON ÉDITORIAL : {strategy.get('tone', 'professionnel')}
CTA PRINCIPAL : {strategy.get('cta_primary', 'Demander un devis')}
MOTS-CLÉS : {safe_string(data.get('keywords', []))}

Rédige :
- 1 H1 accrocheur
- 2-3 H2 avec contenu (50-80 mots chacun)
- 1 paragraphe d'introduction (60-80 mots)
- Le CTA adapté à la page

Format : texte structuré avec titres H1/H2 clairs. Pas de JSON."""

        content = self.llm.generate(prompt, expect_json=False)

        if not content:
            return f"*Contenu à rédiger pour la page {page['name']} — {company} à {city}*"

        return content

    def _generate_design_section(self, data: dict) -> str:
        branding = data.get("branding", {})
        colors   = branding.get("colors", [])
        styles   = branding.get("style", [])

        colors_md = "\n".join(f"- {c}" for c in colors if c) or "- À définir"
        styles_md = "\n".join(
            f"- {s.get('name', s) if isinstance(s, dict) else s}"
            for s in styles
        ) or "- À définir"

        prompt = f"""En tant qu'expert UI/UX, donne des recommandations design courtes pour ce site :
Entreprise : {data.get('company_name', '')} — {data.get('activity', '')}
Couleurs existantes : {', '.join(str(c) for c in colors if c)}
Style : {', '.join(s.get('name', '') if isinstance(s, dict) else str(s) for s in styles)}

Donne 5 recommandations concrètes (typographie, layout, images, UX mobile, accessibilité).
Format texte simple avec tirets."""

        design_reco = self.llm.generate(prompt, expect_json=False)
        if not design_reco:
            design_reco = "- Design responsive mobile-first\n- Typographie lisible\n- Images de qualité"

        return f"""## 4. RECOMMANDATIONS DESIGN

### Charte graphique existante
**Couleurs :**
{colors_md}

**Style :**
{styles_md}

### Recommandations UI/UX
{design_reco}"""

    def _generate_seo_section(self, data: dict) -> str:
        keywords = safe_list(data.get("keywords", []))
        kw_md    = "\n".join(f"- {k}" for k in keywords) or "- À définir"
        strategy = data.get("strategy", {})

        return f"""## 5. STRATÉGIE SEO

### Mots-clés cibles
{kw_md}

### Angle SEO
{strategy.get('seo_angle', 'À définir')}

### Recommandations SEO on-page
- Balises title uniques par page (50-60 caractères)
- Meta descriptions optimisées (150-160 caractères)
- Structure H1 > H2 > H3 respectée
- Images avec attributs alt descriptifs
- URL courtes et descriptives
- Contenu minimum 300 mots par page
- Maillage interne entre les pages
- Page Google My Business à créer/optimiser"""

    def _generate_technical_section(self, data: dict) -> str:
        social = data.get("social", {})
        social_md = "\n".join(
            f"- **{k.capitalize()} :** {v}"
            for k, v in social.items()
            if v and v not in ("", "à créer")
        ) or "- Réseaux sociaux à configurer"

        return f"""## 6. RECOMMANDATIONS TECHNIQUES

### Réseaux sociaux à intégrer
{social_md}

### Fonctionnalités requises
- Formulaire de contact avec validation
- Intégration Google Maps
- Boutons de partage réseaux sociaux
- Optimisation Core Web Vitals
- HTTPS obligatoire
- Politique de confidentialité (RGPD)
- Mentions légales
- Sitemap XML
- Google Analytics / Search Console

### Compatibilité
- Mobile-first (responsive)
- Navigateurs : Chrome, Firefox, Safari, Edge
- Temps de chargement < 3 secondes

### Livrables attendus
- Maquettes (desktop + mobile)
- Site développé et testé
- Formation utilisation CMS
- Documentation technique
- 1 mois de support après livraison"""
    
    def _generate_brief_section(self, data: dict) -> str:
        brief = data.get("brief")
        if not brief:
            return ""

        paragraphes = brief.get("paragraphes", [])
        paragraphes_md = "\n\n".join(
            f"> {p}" for p in paragraphes if p
        )

        idees = brief.get("idees_visuelles", [])
        idees_md = "\n".join(f"- {i}" for i in idees if i)

        return f"""## 0. BRIEF CRÉATIF

### Résumé du site
{brief.get('resume_site', '—')}

### Positionnement
{brief.get('idee_generale', '—')}

### Angle rédactionnel
{brief.get('angle_redac', '—')}

### Paragraphes marketing
{paragraphes_md if paragraphes_md else '—'}

### Idées visuelles
{idees_md if idees_md else '—'}

---"""