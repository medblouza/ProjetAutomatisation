"""
app/streamlit_sitegen_tab.py

Onglet Streamlit : Generation de site a partir d'un cahier des charges.

1. Upload CDC (PDF/DOCX/TXT)
2. Analyse (appel API /site-generator/generate)
   -> affiche entreprise, pages detectees, branding, sections
3. Preview HTML (st.components.v1.html)
4. Download ZIP (st.download_button)
"""
import logging
import os

import requests
import streamlit as st

logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/site-gen")


# ---------------------------------------------------------------------------
# Extraction de texte depuis le fichier uploade
# ---------------------------------------------------------------------------

def _extract_text_from_txt(uploaded_file) -> str:
    return uploaded_file.read().decode("utf-8", errors="ignore")


def _extract_text_from_pdf(uploaded_file) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        st.error("Le package 'pypdf' n'est pas installe (pip install pypdf).")
        return ""

    reader = PdfReader(uploaded_file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_text_from_docx(uploaded_file) -> str:
    try:
        from docx import Document
    except ImportError:
        st.error("Le package 'python-docx' n'est pas installe (pip install python-docx).")
        return ""

    document = Document(uploaded_file)
    return "\n".join(p.text for p in document.paragraphs)


def _extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return _extract_text_from_pdf(uploaded_file)
    if name.endswith(".docx"):
        return _extract_text_from_docx(uploaded_file)
    return _extract_text_from_txt(uploaded_file)


# ---------------------------------------------------------------------------
# Rendu de l'onglet
# ---------------------------------------------------------------------------

def render_sitegen_tab() -> None:
    st.header("🌐 Generation de site web")
    st.caption("Transformez un cahier des charges en site HTML telechargeable.")

    uploaded_file = st.file_uploader(
        "Upload CDC (PDF/DOCX/TXT)",
        type=["pdf", "docx", "txt"],
        key="sitegen_upload",
    )

    if uploaded_file is not None:
        cdc_text = _extract_text(uploaded_file)
        st.session_state["sitegen_cdc_text"] = cdc_text

        if cdc_text.strip():
            with st.expander("Texte extrait du CDC"):
                st.text_area(
                    "Contenu",
                    cdc_text,
                    height=200,
                    key="sitegen_extracted_text",
                    label_visibility="collapsed",
                )
        else:
            st.warning("Aucun texte n'a pu etre extrait de ce fichier.")

    if st.button("Analyze CDC", key="sitegen_analyze_btn", type="primary"):
        cdc_text = st.session_state.get("sitegen_cdc_text", "")
        if not cdc_text.strip():
            st.warning("Veuillez d'abord uploader un fichier CDC contenant du texte.")
        else:
            with st.spinner("Generation du site en cours..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/generate",
                        json={"text": cdc_text},
                        timeout=180,
                    )
                    response.raise_for_status()
                    st.session_state["sitegen_result"] = response.json()
                except requests.RequestException as exc:
                    logger.error("[SitegenTab] Erreur API : %s", exc)
                    st.error(f"Erreur lors de l'appel a l'API : {exc}")

    _render_result()


def _render_result() -> None:
    result = st.session_state.get("sitegen_result")
    if not result:
        return

    cdc = result.get("cdc", {})
    structure = result.get("structure", {})
    routes = structure.get("routes", [])

    st.subheader("📋 Resultat de l'analyse")

    company = cdc.get("company", {})
    branding = cdc.get("branding", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Entreprise**")
        st.write(f"Nom : {company.get('name') or '—'}")
        st.write(f"Activite : {company.get('activity') or '—'}")
        st.write(f"Localisation : {company.get('location') or '—'}")

        st.markdown("**Branding**")
        colors = branding.get("colors") or []
        if colors:
            st.write("Couleurs :")
            for color in colors:
                st.color_picker(color, value=color, key=f"sitegen_color_{color}", disabled=True, label_visibility="collapsed")
        else:
            st.write("Couleurs : —")
        st.write(f"Style : {branding.get('style') or '—'}")
        st.write(f"Typographie : {branding.get('typography') or '—'}")

    with col2:
        st.markdown("**Pages detectees**")
        if routes:
            for route in routes:
                st.write(f"- `{route['page']}` ({route['url']})")
        else:
            st.write("Aucune page detectee.")

        st.markdown("**Sections par page**")
        if routes:
            for route in routes:
                sections = route.get("sections", [])
                names = ", ".join(s.get("name", "") for s in sections if s.get("name")) or "—"
                st.write(f"- `{route['page']}` : {names}")
        else:
            st.write("—")

    st.subheader("👀 Apercu du site")
    st.components.v1.html(result.get("preview_html", ""), height=800, scrolling=True)

    st.subheader("📦 Telechargement")
    download_url = f"{API_BASE_URL}{result['download_url']}"
    try:
        zip_response = requests.get(download_url, timeout=60)
        zip_response.raise_for_status()
        st.download_button(
            "Download Site",
            data=zip_response.content,
            file_name="site.zip",
            mime="application/zip",
            key="sitegen_download_btn",
        )
    except requests.RequestException as exc:
        logger.error("[SitegenTab] Erreur telechargement : %s", exc)
        st.error(f"Erreur lors du telechargement du ZIP : {exc}")
