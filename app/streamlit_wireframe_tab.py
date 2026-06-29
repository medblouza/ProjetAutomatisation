import streamlit as st
import requests
import time

API_BASE = "http://127.0.0.1:8000/api"


def render_wireframe_tab():
    st.header("🎨 Wireframe Generator")
    st.caption("Génération automatique du wireframe depuis les données nettoyées")

    st.divider()

    # ── Données disponibles ? ─────────────────────────────────
    cleaned_data = st.session_state.get("cleaned_data")

    if not cleaned_data:
        st.info("💡 Lance d'abord **Récupérer données** puis **Nettoyer données** dans l'onglet 📊 DP Explorer.")
        st.stop()

    # ── Récap ─────────────────────────────────────────────────
    branding = cleaned_data.get("branding", {})
    colors   = branding.get("colors", [])
    styles   = branding.get("style", [])
    pages    = cleaned_data.get("pages", [])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Client", cleaned_data.get("company_name", "—"))
    with c2:
        st.metric("Pages", len(pages))
    with c3:
        style_names = ", ".join(s.get("name", "") for s in styles) if styles else "—"
        st.metric("Style", style_names)

    # Swatches couleurs
    if colors:
        sw1, sw2, *_ = st.columns(len(colors) + 4)
        with sw1:
            st.markdown(
                f'<div style="background:{colors[0]};height:28px;border-radius:5px;'
                f'border:1px solid #ccc;margin-top:4px"></div>'
                f'<p style="font-size:11px;text-align:center;margin-top:3px">{colors[0]}</p>',
                unsafe_allow_html=True,
            )
        if len(colors) > 1:
            with sw2:
                st.markdown(
                    f'<div style="background:{colors[1]};height:28px;border-radius:5px;'
                    f'border:1px solid #ccc;margin-top:4px"></div>'
                    f'<p style="font-size:11px;text-align:center;margin-top:3px">{colors[1]}</p>',
                    unsafe_allow_html=True,
                )

    # Aperçu du sitemap
    with st.expander("📋 Sitemap détecté", expanded=True):
        for i, page in enumerate(pages):
            st.markdown(f"**{i+1}. {page['name']}**")
            content = page.get("content", "")
            if content:
                st.caption(content[:180] + ("…" if len(content) > 180 else ""))

    st.divider()

    # ── Bouton génération ─────────────────────────────────────
    if st.button("🚀 Générer le Wireframe", type="primary", use_container_width=True):
        _run_generation(cleaned_data)

    # ── Résultat ──────────────────────────────────────────────
    if "last_wireframe" in st.session_state:
        _render_result(st.session_state["last_wireframe"])


# ──────────────────────────────────────────────────────────────

def _run_generation(cleaned_data: dict):
    pages = cleaned_data.get("pages", [])
    n     = len(pages)

    progress = st.progress(0, text="Initialisation…")
    status   = st.empty()

    try:
        for i, page in enumerate(pages):
            pct = int((i / n) * 70) + 5
            progress.progress(pct, text=f"🤖 Structure de « {page['name']} »… ({i+1}/{n})")
            time.sleep(0.1)  # juste pour l'UX, le vrai temps est côté API

        progress.progress(80, text="📐 Finalisation de la structure…")

        r = requests.post(
            f"{API_BASE}/generate-wireframe",
            json={"cleaned_data": cleaned_data},
            timeout=180,
        )

        progress.progress(95, text="🎨 Génération du HTML…")
        time.sleep(0.3)
        progress.progress(100, text="✅ Wireframe prêt !")

        if r.ok:
            result = r.json()
            st.session_state["last_wireframe"] = result
            status.success(
                f"✅ **{result['project_name']}** — "
                f"{result['pages_count']} pages générées"
            )
            st.rerun()
        else:
            detail = r.json().get("detail", r.text)
            status.error(f"❌ {detail}")
            progress.empty()

    except requests.exceptions.Timeout:
        status.error("⏱ Timeout — le backend a mis trop de temps (>180s).")
        progress.empty()
    except Exception as e:
        status.error(f"❌ Erreur inattendue : {e}")
        progress.empty()


def _render_result(result: dict):
    st.divider()
    st.subheader("🎉 Wireframe généré")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Pages", result["pages_count"])
    with m2:
        st.metric("Style", result.get("style", {}).get("style", "—"))
    with m3:
        st.metric("Format", "HTML")

    # Téléchargement
    st.download_button(
        label="⬇️ Télécharger le wireframe (.html)",
        data=result["html"].encode("utf-8"),
        file_name=f"wireframe_{result['project_name'].replace(' ', '_')}.html",
        mime="text/html",
        use_container_width=True,
    )

    # Structure
    with st.expander("📋 Structure générée par l'agent", expanded=False):
        for page in result.get("pages", []):
            st.markdown(f"**📄 {page['name']}**")
            for s in page.get("sections", []):
                height = f" — {s['height']}px" if s.get("height") else ""
                desc   = f" · {s['description']}" if s.get("description") else ""
                st.markdown(f"  `{s['type'].upper()}` {s['name']}{height}{desc}")

    # Aperçu iframe
    st.subheader("🖼️ Aperçu interactif")
    st.components.v1.html(result["html"], height=750, scrolling=True)

    # Reset
    st.divider()
    if st.button("🔄 Régénérer", type="secondary"):
        del st.session_state["last_wireframe"]
        st.rerun()