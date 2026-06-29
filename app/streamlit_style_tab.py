import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/api/style/extract"

def render_style_tab():
    st.title("🖌️ Style Extractor")
    st.caption("Upload 2 à 5 captures de référence — l'IA analyse le style visuel automatiquement.")
    st.divider()

    uploaded_files = st.file_uploader(
        "Ajoute tes références visuelles",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        help="2 images minimum, 5 maximum",
        key="style_uploader"
    )

    if uploaded_files:
        st.write(f"**{len(uploaded_files)} image(s) chargée(s)**")
        cols = st.columns(min(len(uploaded_files), 4))
        for i, f in enumerate(uploaded_files):
            with cols[i % 4]:
                st.image(f, caption=f.name, use_container_width=True)


    st.divider()

    btn_disabled = not uploaded_files or len(uploaded_files) < 1
    if btn_disabled and uploaded_files:
        st.warning("Ajoute au moins **2 images** pour lancer l'extraction.")

    if st.button("✦ Extraire le style", disabled=btn_disabled, type="primary", key="style_btn"):
        with st.spinner("Analyse en cours..."):
            files_payload = [("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files]
            try:
                response = requests.post(API_URL, files=files_payload, timeout=60)
                response.raise_for_status()
                style = response.json()
            except requests.exceptions.ConnectionError:
                st.error("Impossible de joindre l'API. Vérifie que FastAPI tourne sur le port 8000.")
                return
            except requests.exceptions.HTTPError as e:
                st.error(f"Erreur API : {e.response.json().get('detail', str(e))}")
                return

        st.success("✅ Style extrait avec succès !")
        st.subheader("Résultats")

        # Palette
        st.write("**Palette de couleurs**")
        palette = style.get("palette", [])
        if palette:
            pcols = st.columns(len(palette))
            for col, hex_color in zip(pcols, palette):
                col.markdown(
                    f'<div style="background:{hex_color};height:60px;border-radius:10px;'
                    f'margin-bottom:6px;border:1px solid rgba(0,0,0,0.08)"></div>'
                    f'<p style="text-align:center;font-size:12px;font-family:monospace;margin:0">{hex_color}</p>',
                    unsafe_allow_html=True,
                )

        st.write("")
        col1, col2, col3, col4 = st.columns(4)
        typo = style.get("typography", {})
        col1.metric("Typographie", typo.get("style", "—"))
        col2.metric("Densité UI", style.get("density", "—"))
        col3.metric("Style visuel", style.get("visual_style", "—"))
        col4.metric("Contraste typo", typo.get("contrast", "—"))

        mood = style.get("dominant_mood", "")
        if mood:
            st.info(f"✦ **Ambiance dominante :** {mood}")

        with st.expander("Voir le détail par référence"):
            for i, ref in enumerate(style.get("styles_per_ref", [])):
                st.write(f"**Référence {i+1}**")
                ref_palette = ref.get("colors", [])
                if ref_palette:
                    swatch_html = "".join(
                        f'<span style="display:inline-block;width:24px;height:24px;border-radius:4px;'
                        f'background:{c};margin-right:4px;border:1px solid rgba(0,0,0,0.1)"></span>'
                        for c in ref_palette
                    )
                    st.markdown(swatch_html, unsafe_allow_html=True)
                st.write(f"Densité : `{ref.get('density','—')}` | Style : `{ref.get('visual_style','—')}`")
                st.write(f"Ambiance : *{ref.get('dominant_mood','—')}*")
                st.divider()

        with st.expander("JSON brut"):
            st.json(style)