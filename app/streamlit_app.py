'''
import streamlit as st
import requests

# ─── Config ─────────────────────────────────────────
st.set_page_config(page_title="DP Explorer", page_icon="🔍")

API_BASE = "http://127.0.0.1:8000"

# ─── Session ────────────────────────────────────────
if "auth" not in st.session_state:
    st.session_state.auth = None
if "result" not in st.session_state:
    st.session_state.result = None
if "cdc" not in st.session_state:
    st.session_state.cdc = None

# ─── Sidebar ────────────────────────────────────────
st.sidebar.title("🔧 Configuration")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

# ─── LOGIN (via FastAPI) ────────────────────────────
if st.sidebar.button("Connexion"):
    try:
        res = requests.post(
            f"{API_BASE}/login",
            json={
                "username": username,
                "password": password
            },
            timeout=10
        )

        if res.status_code == 200:
            st.session_state.auth = {
                "username": username,
                "password": password
            }
            st.sidebar.success("Connecté")
        else:
            st.sidebar.error("Erreur login")

    except Exception as e:
        st.sidebar.error(f"Erreur API : {e}")

# ─── Déconnexion ────────────────────────────────────
if st.session_state.auth:
    if st.sidebar.button("Déconnexion"):
        st.session_state.auth = None
        st.session_state.result = None
        st.session_state.cdc = None
        st.rerun()

# ─── MAIN ───────────────────────────────────────────
st.title("📊 DP Data Explorer")

code = st.text_input("Code client (Code Sage)")

col1, col2 = st.columns(2)

# ─── 1. Récupérer données ───────────────────────────
with col1:
    if st.button("🔍 Récupérer données"):

        if not st.session_state.auth:
            st.error("Connecte-toi d'abord")
        elif not code:
            st.warning("Entre un code")
        else:
            with st.spinner("Chargement..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/info",
                        json={
                            "username": st.session_state.auth["username"],
                            "password": st.session_state.auth["password"],
                            "code": code
                        },
                        timeout=60
                    )

                    if res.status_code == 200:
                        st.session_state.result = res.json()
                    else:
                        st.error(res.json().get("detail", "Erreur API"))

                except Exception as e:
                    st.error(f"Erreur connexion API : {e}")

# ─── 2. Générer CDC ────────────────────────────────
with col2:
    if st.button("🧾 Générer Cahier de charge"):

        if not st.session_state.auth:
            st.error("Connecte-toi d'abord")
        elif not code:
            st.warning("Entre un code")
        else:
            with st.spinner("Génération du cahier de charge..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/process",
                        json={
                            "username": st.session_state.auth["username"],
                            "password": st.session_state.auth["password"],
                            "code": code
                        },
                        timeout=120
                    )

                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.cdc = data.get("result", data)
                        st.session_state.qa = data.get("qa", {})
                    else:
                        st.error(res.json().get("detail", "Erreur API"))

                except Exception as e:
                    st.error(f"Erreur connexion API : {e}")

# ─── RESULTATS DATA ────────────────────────────────
if st.session_state.result:

    data = st.session_state.result

    st.subheader("📌 Résumé")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Enseigne", data.get("company", {}).get("Name", "—"))

    with col2:
        st.metric("Secteur", data.get("company", {}).get("Industry", "—"))

    with col3:
        st.metric("Ville", data.get("company", {}).get("BillingCity", "—"))

    st.divider()

    st.subheader("📦 Données complètes")

    with st.expander("Partner"):
        st.json(data.get("partner", {}))

    with st.expander("Details"):
        st.json(data.get("details", {}))

    with st.expander("Company"):
        st.json(data.get("company", {}))

# ─── RESULTATS CDC ────────────────────────────────
if st.session_state.cdc:

    st.divider()
    st.subheader("📄 Cahier de charge généré")

    if "qa" in st.session_state:
        qa = st.session_state.qa
        st.info(f"Score qualité : {qa.get('score', 'N/A')}")

    st.text_area(
        "CDC",
        st.session_state.cdc,
        height=400
    )

    st.download_button(
        label="📥 Télécharger le CDC",
        data=st.session_state.cdc,
        file_name="cahier_de_charge.txt"
    )
'''
import streamlit as st
import requests

# ─── Config ─────────────────────────────────────────
st.set_page_config(page_title="DP Explorer", page_icon="🔍")

API_BASE = "http://127.0.0.1:8000"

# ─── Session ────────────────────────────────────────
if "auth" not in st.session_state:
    st.session_state.auth = None
if "result" not in st.session_state:
    st.session_state.result = None
if "cdc" not in st.session_state:
    st.session_state.cdc = None
if "cleaned" not in st.session_state:
    st.session_state.cleaned = None

# ─── Sidebar ────────────────────────────────────────
st.sidebar.title("🔧 Configuration")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

# ─── LOGIN ──────────────────────────────────────────
if st.sidebar.button("Connexion"):
    try:
        res = requests.post(
            f"{API_BASE}/login",
            json={
                "username": username,
                "password": password
            },
            timeout=10
        )

        if res.status_code == 200:
            st.session_state.auth = {
                "username": username,
                "password": password
            }
            st.sidebar.success("Connecté")
        else:
            st.sidebar.error("Erreur login")

    except Exception as e:
        st.sidebar.error(f"Erreur API : {e}")

# ─── Déconnexion ────────────────────────────────────
if st.session_state.auth:
    if st.sidebar.button("Déconnexion"):
        st.session_state.auth = None
        st.session_state.result = None
        st.session_state.cdc = None
        st.session_state.cleaned = None
        st.rerun()

# ─── MAIN ───────────────────────────────────────────
st.title("📊 DP Data Explorer")

code = st.text_input("Code client (Code Sage)")

# 🔥 3 boutons maintenant
col1, col2, col3 = st.columns(3)

# ─── 1. Récupérer données ───────────────────────────
with col1:
    if st.button("🔍 Récupérer données"):

        if not st.session_state.auth:
            st.error("Connecte-toi d'abord")
        elif not code:
            st.warning("Entre un code")
        else:
            with st.spinner("Chargement..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/info",
                        json={
                            "username": st.session_state.auth["username"],
                            "password": st.session_state.auth["password"],
                            "code": code
                        },
                        timeout=60
                    )

                    if res.status_code == 200:
                        st.session_state.result = res.json()
                    else:
                        st.error(res.json().get("detail", "Erreur API"))

                except Exception as e:
                    st.error(f"Erreur connexion API : {e}")

# ─── 2. Générer CDC ────────────────────────────────
with col2:
    if st.button("🧾 Générer Cahier de charge"):

        if not st.session_state.auth:
            st.error("Connecte-toi d'abord")
        elif not code:
            st.warning("Entre un code")
        else:
            with st.spinner("Génération du cahier de charge..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/generate-cdc",  # ✅ changé ici
                        json={
                            "username": st.session_state.auth["username"],
                            "password": st.session_state.auth["password"],
                            "code": code
                        },
                        timeout=120
                    )

                    if res.status_code == 200:
                        data = res.json()

                        # ✅ adapter au nouveau format
                        st.session_state.cdc = data.get("content")
                        st.session_state.qa = {
                            "score": data.get("score")
                        }

                    else:
                        st.error(res.json().get("detail", "Erreur API"))

                except Exception as e:
                    st.error(f"Erreur connexion API : {e}")

# ─── 3. Nettoyer données 🧹 ─────────────────────────
with col3:
    if st.button("🧹 Nettoyer données"):

        if not st.session_state.auth:
            st.error("Connecte-toi d'abord")
        elif not code:
            st.warning("Entre un code")
        else:
            with st.spinner("Nettoyage..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/clean",
                        json={
                            "username": st.session_state.auth["username"],
                            "password": st.session_state.auth["password"],
                            "code": code
                        },
                        timeout=60
                    )

                    if res.status_code == 200:
                        st.session_state.cleaned = res.json().get("cleaned")
                    else:
                        st.error(res.json().get("detail", "Erreur API"))

                except Exception as e:
                    st.error(f"Erreur : {e}")

# ─── RESULTATS DATA ────────────────────────────────
if st.session_state.result:

    data = st.session_state.result

    st.subheader("📌 Résumé")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Enseigne", data.get("company", {}).get("Name", "—"))

    with col2:
        st.metric("Secteur", data.get("company", {}).get("Industry", "—"))

    with col3:
        st.metric("Ville", data.get("company", {}).get("BillingCity", "—"))

    st.divider()

    st.subheader("📦 Données complètes")

    with st.expander("Partner"):
        st.json(data.get("partner", {}))

    with st.expander("Details"):
        st.json(data.get("details", {}))

    with st.expander("Company"):
        st.json(data.get("company", {}))

# ─── RESULTATS CLEAN ────────────────────────────────
if st.session_state.cleaned:

    st.divider()
    st.subheader("🧹 Données nettoyées")

    st.json(st.session_state.cleaned)

# ─── RESULTATS CDC ────────────────────────────────
if st.session_state.cdc:

    st.divider()
    st.subheader("📄 Cahier de charge généré")

    if "qa" in st.session_state:
        qa = st.session_state.qa
        st.info(f"Score qualité : {qa.get('score', 'N/A')}")

    st.text_area(
        "CDC",
        st.session_state.cdc,
        height=400
    )

    st.download_button(
        label="📥 Télécharger le CDC",
        data=st.session_state.cdc,
        file_name="cahier_de_charge.txt"
    )