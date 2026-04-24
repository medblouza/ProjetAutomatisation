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
'''
import math
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

# Dropbox
if "dbx_access_token" not in st.session_state:
    st.session_state.dbx_access_token = ""
if "dbx_files" not in st.session_state:
    st.session_state.dbx_files = []
if "dbx_current_path" not in st.session_state:
    st.session_state.dbx_current_path = ""
if "dbx_path_history" not in st.session_state:
    st.session_state.dbx_path_history = []
if "dbx_auth_url" not in st.session_state:
    st.session_state.dbx_auth_url = ""
if "dbx_auth_state" not in st.session_state:
    st.session_state.dbx_auth_state = ""

# ─── Sidebar ────────────────────────────────────────
st.sidebar.title("🔧 Configuration")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

# ─── LOGIN ──────────────────────────────────────────
if st.sidebar.button("Connexion"):
    try:
        res = requests.post(
            f"{API_BASE}/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if res.status_code == 200:
            st.session_state.auth = {"username": username, "password": password}
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

# ─── Dropbox statut sidebar ─────────────────────────
st.sidebar.divider()
if st.session_state.dbx_access_token:
    st.sidebar.success("📦 Dropbox connecté")
    if st.sidebar.button("🔓 Déconnecter Dropbox"):
        st.session_state.dbx_access_token = ""
        st.session_state.dbx_files = []
        st.session_state.dbx_current_path = ""
        st.session_state.dbx_path_history = []
        st.session_state.dbx_auth_url = ""
        st.session_state.dbx_auth_state = ""
        st.rerun()
else:
    st.sidebar.info("📦 Dropbox non connecté")

# ─── TABS ────────────────────────────────────────────
tab_dp, tab_dbx = st.tabs(["📊 DP Explorer", "📦 Dropbox"])


# ════════════════════════════════════════════════════
# TAB 1 — DP Explorer (ton code existant)
# ════════════════════════════════════════════════════
with tab_dp:

    st.title("📊 DP Data Explorer")

    code = st.text_input("Code client (Code Sage)")

    col1, col2, col3 = st.columns(3)

    # ─── 1. Récupérer données ───────────────────────
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
                                "code": code,
                            },
                            timeout=60,
                        )
                        if res.status_code == 200:
                            st.session_state.result = res.json()
                        else:
                            st.error(res.json().get("detail", "Erreur API"))
                    except Exception as e:
                        st.error(f"Erreur connexion API : {e}")

    # ─── 2. Générer CDC ─────────────────────────────
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
                            f"{API_BASE}/generate-cdc",
                            json={
                                "username": st.session_state.auth["username"],
                                "password": st.session_state.auth["password"],
                                "code": code,
                            },
                            timeout=120,
                        )
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.cdc = data.get("content")
                            st.session_state.qa = {"score": data.get("score")}
                        else:
                            st.error(res.json().get("detail", "Erreur API"))
                    except Exception as e:
                        st.error(f"Erreur connexion API : {e}")

    # ─── 3. Nettoyer données ─────────────────────────
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
                                "code": code,
                            },
                            timeout=60,
                        )
                        if res.status_code == 200:
                            st.session_state.cleaned = res.json().get("cleaned")
                        else:
                            st.error(res.json().get("detail", "Erreur API"))
                    except Exception as e:
                        st.error(f"Erreur : {e}")

    # ─── Résultats DATA ─────────────────────────────
    if st.session_state.result:
        data = st.session_state.result
        st.subheader("📌 Résumé")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Enseigne", data.get("company", {}).get("Name", "—"))
        with c2:
            st.metric("Secteur", data.get("company", {}).get("Industry", "—"))
        with c3:
            st.metric("Ville", data.get("company", {}).get("BillingCity", "—"))
        st.divider()
        st.subheader("📦 Données complètes")
        with st.expander("Partner"):
            st.json(data.get("partner", {}))
        with st.expander("Details"):
            st.json(data.get("details", {}))
        with st.expander("Company"):
            st.json(data.get("company", {}))

    # ─── Résultats CLEAN ────────────────────────────
    if st.session_state.cleaned:
        st.divider()
        st.subheader("🧹 Données nettoyées")
        st.json(st.session_state.cleaned)

    # ─── Résultats CDC ──────────────────────────────
    if st.session_state.cdc:
        st.divider()
        st.subheader("📄 Cahier de charge généré")
        if "qa" in st.session_state:
            st.info(f"Score qualité : {st.session_state.qa.get('score', 'N/A')}")
        st.text_area("CDC", st.session_state.cdc, height=400)
        st.download_button(
            label="📥 Télécharger le CDC",
            data=st.session_state.cdc,
            file_name="cahier_de_charge.txt",
        )


# ════════════════════════════════════════════════════
# TAB 2 — Dropbox
# ════════════════════════════════════════════════════
with tab_dbx:

    st.title("📦 Dropbox")

    # ── Helpers ──────────────────────────────────────
    def fmt_size(n: int) -> str:
        if not n:
            return "—"
        units = ["o", "Ko", "Mo", "Go"]
        i = min(int(math.log(n, 1024)), len(units) - 1)
        return f"{n / (1024 ** i):.1f} {units[i]}"

    def file_icon(f: dict) -> str:
        if f.get("is_folder"):
            return "📁"
        name = f.get("name", "").lower()
        if name.endswith(".pdf"):                          return "📄"
        if name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")): return "🖼️"
        if name.endswith((".mp4", ".mov")):               return "🎬"
        if name.endswith((".mp3", ".wav")):               return "🎵"
        if name.endswith((".zip", ".tar", ".gz")):        return "🗜️"
        if name.endswith((".xlsx", ".xls", ".csv")):      return "📊"
        if name.endswith((".docx", ".doc")):              return "📝"
        if name.endswith((".py", ".js", ".json")):        return "💻"
        return "📎"

    def load_files(path: str):
        with st.spinner("Chargement..."):
            try:
                res = requests.post(
                    f"{API_BASE}/dropbox/list",
                    json={
                        "access_token": st.session_state.dbx_access_token,
                        "path": path,
                        "recursive": False,
                    },
                    timeout=30,
                )
                if res.status_code == 200:
                    st.session_state.dbx_files = res.json().get("files", [])
                    st.session_state.dbx_current_path = path
                else:
                    st.error(res.json().get("detail", "Erreur API"))
            except Exception as e:
                st.error(f"Erreur : {e}")

    def search_files(query: str):
        with st.spinner("Recherche..."):
            try:
                res = requests.post(
                    f"{API_BASE}/dropbox/search",
                    json={
                        "access_token": st.session_state.dbx_access_token,
                        "query": query,
                        "path": "",
                    },
                    timeout=30,
                )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.dbx_files = data.get("files", [])
                    st.info(f"{data.get('total', 0)} résultat(s) pour « {query} »")
                else:
                    st.error(res.json().get("detail", "Erreur API"))
            except Exception as e:
                st.error(f"Erreur : {e}")

    # ── Authentification ─────────────────────────────
    if not st.session_state.dbx_access_token:

        st.info("Connecte-toi à Dropbox pour accéder à tes fichiers.")

        col_a, col_b = st.columns([2, 1])

        with col_a:
            if st.button("🔗 Se connecter à Dropbox", use_container_width=True):
                try:
                    res = requests.get(f"{API_BASE}/dropbox/auth-url", timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.dbx_auth_url   = data["auth_url"]
                        st.session_state.dbx_auth_state = data["state"]
                    else:
                        st.error("Impossible d'obtenir l'URL d'auth.")
                except Exception as e:
                    st.error(f"Erreur API : {e}")

            if st.session_state.dbx_auth_url:
                st.markdown(
                    f"**1.** [Clique ici pour autoriser l'accès Dropbox]({st.session_state.dbx_auth_url})"
                )
                st.markdown("**2.** Copie le code affiché après l'autorisation et colle-le ci-dessous :")

                auth_code = st.text_input("Code d'autorisation", placeholder="sl.AbCdEf...")

                if st.button("✅ Valider le code", use_container_width=True):
                    if not auth_code.strip():
                        st.warning("Entre le code d'autorisation.")
                    else:
                        try:
                            res = requests.post(
                                f"{API_BASE}/dropbox/callback",
                                json={
                                    "code":  auth_code.strip(),
                                    "state": st.session_state.dbx_auth_state,
                                },
                                timeout=15,
                            )
                            if res.status_code == 200:
                                tokens = res.json()
                                st.session_state.dbx_access_token = tokens.get("access_token", "")
                                st.success("✅ Connecté à Dropbox !")
                                st.rerun()
                            else:
                                st.error(res.json().get("detail", "Erreur d'authentification."))
                        except Exception as e:
                            st.error(f"Erreur : {e}")

        with col_b:
            st.markdown("#### Comment ça marche ?")
            st.markdown("""
1. Clique **Se connecter**
2. Autorise l'app sur Dropbox
3. Copie le **code** affiché
4. Colle-le et valide
""")

    # ── Interface fichiers ────────────────────────────
    else:

        st.success("✅ Connecté à Dropbox")
        st.divider()

        # Navigation + Recherche
        nav_col, search_col = st.columns([3, 2])

        with nav_col:
            breadcrumb = " › ".join(["🏠 Racine"] + st.session_state.dbx_path_history)
            st.caption(f"📂 {breadcrumb}")

            path_input = st.text_input(
                "Chemin (vide = racine)",
                value=st.session_state.dbx_current_path,
                placeholder="/Mon Dossier",
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("📂 Lister", use_container_width=True):
                    load_files(path_input.strip())
            with c2:
                if st.session_state.dbx_path_history:
                    if st.button("⬅️ Retour", use_container_width=True):
                        st.session_state.dbx_path_history.pop()
                        parent = "/".join(
                            st.session_state.dbx_current_path.rsplit("/", 1)[:-1]
                        ) or ""
                        load_files(parent)

        with search_col:
            search_query = st.text_input("🔍 Recherche", placeholder="rapport 2024...")
            if st.button("Rechercher", use_container_width=True):
                if search_query.strip():
                    search_files(search_query.strip())
                else:
                    st.warning("Entre un terme de recherche.")

        st.divider()

        # Liste des fichiers
        files = st.session_state.dbx_files

        if not files:
            st.info("Clique sur **Lister** pour afficher le contenu de ton Dropbox.")
        else:
            st.markdown(f"**{len(files)} élément(s)**")

            # Filtres
            f1, f2 = st.columns(2)
            with f1:
                filter_type = st.selectbox("Type", ["Tout", "Dossiers", "Fichiers"])
            with f2:
                filter_name = st.text_input("Filtrer par nom", placeholder="budget...")

            filtered = files
            if filter_type == "Dossiers":
                filtered = [f for f in filtered if f.get("is_folder")]
            elif filter_type == "Fichiers":
                filtered = [f for f in filtered if not f.get("is_folder")]
            if filter_name:
                filtered = [f for f in filtered if filter_name.lower() in f.get("name", "").lower()]

            if not filtered:
                st.warning("Aucun élément ne correspond aux filtres.")
            else:
                # En-tête tableau
                h1, h2, h3, h4, h5 = st.columns([0.4, 3.5, 1.2, 1.2, 1.2])
                h2.markdown("**Nom**")
                h3.markdown("**Taille**")
                h4.markdown("**Modifié**")

                st.divider()

                for f in filtered:
                    icon  = file_icon(f)
                    name  = f.get("name", "—")
                    size  = fmt_size(f.get("size", 0))
                    date  = (f.get("modified", "") or "")[:10]
                    path  = f.get("path", "")
                    is_dir = f.get("is_folder", False)

                    c_icon, c_name, c_size, c_date, c_dl = st.columns([0.4, 3.5, 1.2, 1.2, 1.2])

                    with c_icon:
                        st.write(icon)

                    with c_name:
                        if is_dir:
                            if st.button(name, key=f"nav_{path}", use_container_width=True):
                                st.session_state.dbx_path_history.append(name)
                                load_files(path)
                        else:
                            st.write(f"**{name}**")
                            st.caption(path)

                    with c_size:
                        st.write(size)

                    with c_date:
                        st.write(date or "—")

                    with c_dl:
                        if not is_dir:
                            if st.button("⬇️", key=f"dl_{path}", use_container_width=True):
                                with st.spinner(f"Téléchargement..."):
                                    try:
                                        dl_res = requests.post(
                                            f"{API_BASE}/dropbox/download",
                                            json={
                                                "access_token": st.session_state.dbx_access_token,
                                                "path": path,
                                            },
                                            timeout=60,
                                        )
                                        if dl_res.status_code == 200:
                                            st.download_button(
                                                label=f"💾 Sauvegarder",
                                                data=dl_res.content,
                                                file_name=name,
                                                mime=dl_res.headers.get("Content-Type", "application/octet-stream"),
                                                key=f"save_{path}",
                                            )
                                        else:
                                            st.error(dl_res.json().get("detail", "Erreur téléchargement"))
                                    except Exception as e:
                                        st.error(f"Erreur : {e}")

                    st.divider()