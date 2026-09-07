# 🚀 PFE Automatisation — Plateforme IA de Génération de Sites Web

> Projet de Fin d'Études (PFE) — Automatisation de la création de sites web d'entreprises à partir de données métier, via une pipeline d'agents IA.

---

## 📋 Table des matières

- [À propos du projet](#-à-propos-du-projet)
- [Architecture](#-architecture)
- [Fonctionnalités](#-fonctionnalités)
- [Stack technique](#-stack-technique)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Lancement](#-lancement)
- [Structure du projet](#-structure-du-projet)
- [API](#-api)

---

## 🎯 À propos du projet

Cette plateforme automatise la création de sites web professionnels. À partir des données client, elle :

1. **Récupère** les données de l'entreprise depuis l'API **DP LocaletMoi / Local.fr**
2. **Nettoie et analyse** les données via des agents LLM
3. **Génère automatiquement** un cahier des charges (CDC), une charte graphique, des wireframes et le code HTML/CSS final
4. **Exporte** le résultat sous forme de site web complet téléchargeable

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
│  Login │ DP Explorer │ Dropbox │ Wireframe │ Style │ SiteGen │ CDC│
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP / REST
┌────────────────────────────▼─────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐    │
│  │  DP Service │  │ Dropbox Svc  │  │    AI Agent Pipeline  │    │
│  │ (Local.fr)  │  │ (Cloud sync) │  │                        │   │
│  └─────────────┘  └──────────────┘  │  AnalyzerAgent         │   │
│                                     │  BriefAgent            │   │
│  ┌─────────────┐  ┌──────────────┐  │  StrategyAgent         │   │
│  │Style Extract│  │  Figma API   │  │  StructureAgent        │   │
│  │  (CSS/HTML) │  │  (Design)    │  │  ContentAgent          │   │
│  └─────────────┘  └──────────────┘  │  DesignGeneratorAgent  │   │
│                                     │  WireframeAgent        │   │
│  ┌─────────────────────────────┐    │  QAAgent               │   │
│  │     LLM Tool                │    │  SiteGenAgent          │   │
│  │ (Groq / Gemini / OpenRouter)│    └───────────────────────┘   │
│  └─────────────────────────────┘                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │               PostgreSQL Database                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## ✨ Fonctionnalités

| Module | Description |
|--------|-------------|
| 🔑 **Authentification** | Login sécurisé via l'API DP LocaletMoi |
| 🗂️ **DP Explorer** | Exploration et visualisation des données entreprises (pages, variables, médias) |
| 📄 **CDC Generator** | Génération automatique du Cahier des Charges via pipeline multi-agents LLM |
| 📋 **CDC List** | Historique et gestion des CDC générés (sauvegardés en PostgreSQL) |
| 🎨 **Style Extractor** | Extraction de la charte graphique (couleurs, polices, styles) depuis un site existant ou Figma |
| 🖼️ **Wireframe Generator** | Génération de wireframes HTML structurés via agents IA |
| 🌐 **Site Generator** | Génération complète du code HTML/CSS/JS du site final |
| ☁️ **Dropbox Integration** | Synchronisation et gestion des fichiers via Dropbox |
| 💡 **Social Suggester** | Suggestions de contenu pour les réseaux sociaux |

---

## 🛠️ Stack technique

### Backend
| Technologie | Rôle |
|-------------|------|
| **Python 3.11+** | Langage principal |
| **FastAPI** | API REST |
| **PostgreSQL** | Base de données |
| **psycopg2** | Connecteur PostgreSQL |
| **python-docx** | Export DOCX |
| **Groq API** | LLM principal (Llama 3) |
| **Gemini API** | LLM alternatif (Google) |
| **OpenRouter** | Accès multi-modèles (GPT, etc.) |
| **Figma API** | Extraction de designs |
| **Dropbox SDK** | Stockage cloud |
| **Streamlit** | Interface de prototypage (legacy) |

### Frontend
| Technologie | Rôle |
|-------------|------|
| **React 19** | Framework UI |
| **Vite 8** | Build tool |
| **TailwindCSS 4** | Styles |
| **Axios** | Requêtes HTTP |
| **Lucide React** | Icônes |
| **JSZip + FileSaver** | Export de fichiers ZIP |

---

## 📦 Prérequis

- **Python** >= 3.11
- **Node.js** >= 18
- **PostgreSQL** >= 14
- Comptes et clés API :
  - Groq API
  - Gemini API (Google)
  - OpenRouter
  - Figma (token personnel)
  - Dropbox (App Key + Secret)

---

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/<votre-username>/PFE_Automatisation.git
cd PFE_Automatisation
```

### 2. Backend — Environnement Python

```bash
cd app
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend — Dépendances Node

```bash
cd app/frontend
npm install
```

### 4. Base de données PostgreSQL

```sql
CREATE DATABASE "PFE_Automatisation";
```

L'initialisation des tables est effectuée automatiquement au démarrage du backend via `init_db()`.

---

## ⚙️ Configuration

Créez un fichier `app/.env` à partir du modèle suivant :

```env
# Dropbox OAuth
DROPBOX_APP_KEY=<votre_app_key>
DROPBOX_APP_SECRET=<votre_app_secret>
DROPBOX_REDIRECT_URI=http://localhost:8501

# LLM APIs
GROQ_API_KEY=<votre_groq_api_key>
GEMINI_API_KEY=<votre_gemini_api_key>
OPENROUTER_API_KEY=<votre_openrouter_api_key>
OPENROUTER_MODEL=openai/gpt-4o

# Figma
FIGMA_TOKEN=<votre_figma_token>

# Base de données
DATABASE_URL=postgresql://postgres:<mot_de_passe>@localhost:5432/PFE_Automatisation


## ▶️ Lancement

### Backend (FastAPI)

```bash
# Depuis la racine du projet
uvicorn app.main:app --reload --port 8000
```

L'API est accessible sur : `http://localhost:8000`
Documentation interactive (Swagger) : `http://localhost:8000/docs`

### Frontend (React + Vite)

```bash
cd app/frontend
npm run dev
```

L'interface est accessible sur : `http://localhost:5173`

---

## 📁 Structure du projet

```
PFE_Automatisation/
├── app/
│   ├── main.py                    # Point d'entrée FastAPI
│   ├── database.py                # Connexion PostgreSQL & modèles
│   ├── dp_service.py              # Scraping/API Local.fr / DP
│   ├── cleaner.py                 # Nettoyage des données DP
│   ├── social_suggester.py        # Suggestions réseaux sociaux
│   │
│   ├── llm/
│   │   └── llm_tool.py            # Abstraction LLM (Groq/Gemini/OpenRouter)
│   │
│   ├── mcp/
│   │   ├── pipeline.py            # Orchestration du pipeline d'agents
│   │   ├── agents/
│   │   │   ├── base_agent.py      # Agent de base (entrée pipeline)
│   │   │   ├── analyzer_agent.py  # Analyse des données entreprise
│   │   │   ├── brief_agent.py     # Génération du brief créatif
│   │   │   ├── strategy_agent.py  # Stratégie de contenu
│   │   │   ├── structure_agent.py # Structure du site (arborescence)
│   │   │   ├── content_agent.py   # Rédaction du contenu
│   │   │   ├── design_generator_agent.py  # Charte graphique JSON
│   │   │   ├── wireframe_agent.py # Génération des wireframes HTML
│   │   │   ├── qa_agent.py        # Contrôle qualité
│   │   │   └── sitegen/           # Agents de génération de site final
│   │   └── routers/
│   │       ├── design_router.py   # Endpoints design/charte
│   │       └── web_generator_router.py  # Endpoints génération web
│   │
│   ├── services/
│   │   ├── figma_service.py       # Intégration Figma API
│   │   ├── style_extractor.py     # Extraction CSS/charte depuis URL
│   │   ├── llm_service.py         # Wrapper LLM pour services
│   │   └── web_code_generator.py  # Assemblage code final
│   │
│   ├── cdc_router.py              # Endpoints CDC
│   ├── dropbox_router.py          # Endpoints Dropbox
│   ├── wireframe_router.py        # Endpoints wireframes
│   ├── style_extractor_router.py  # Endpoints style
│   │
│   └── frontend/                  # Application React
│       └── src/
│           ├── pages/
│           │   ├── Login.jsx
│           │   ├── DPExplorer.jsx
│           │   ├── CDCList.jsx
│           │   ├── Wireframe.jsx
│           │   ├── StyleExtractor.jsx
│           │   ├── SiteGenerator.jsx
│           │   └── Dropbox.jsx
│           ├── hooks/
│           │   ├── useAuth.jsx
│           │   └── useNotification.jsx
│           ├── layouts/
│           │   └── DashboardLayout.jsx
│           └── services/          # Appels API Axios
│
├── storage/                       # Fichiers générés (wireframes, sites...)
├── package.json
└── README.md
```

---

## 🔌 API

Les principaux endpoints exposés par le backend :

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/login` | Authentification via DP |
| `POST` | `/info` | Récupération des données d'une entreprise par code |
| `POST` | `/process` | Traitement complet des données DP |
| `POST` | `/clean` | Nettoyage des données brutes |
| `POST` | `/generate-cdc` | Génération du cahier des charges via LLM |
| `POST` | `/suggest-social` | Suggestions de posts réseaux sociaux |
| `POST` | `/api/download-docx` | Export du CDC au format Word (.docx) |
| `GET/POST` | `/api/wireframe/*` | Génération et récupération de wireframes |
| `GET/POST` | `/api/style/*` | Extraction de charte graphique |
| `GET/POST` | `/api/cdc/*` | CRUD CDC en base PostgreSQL |
| `GET/POST` | `/dropbox/*` | Opérations Dropbox |

> Documentation complète disponible sur `http://localhost:8000/docs` (Swagger UI).

---

## 🤖 Pipeline d'agents IA

Le cœur du projet repose sur une pipeline d'agents LLM séquentiels  :

```
Données DP brutes
      │
      ▼
 BaseAgent (entrée)
      │
      ▼
 AnalyzerAgent → analyse sectorielle & concurrentielle
      │
      ▼
 BriefAgent → brief créatif (ton, valeurs, audience)
      │
      ▼
 StrategyAgent → stratégie de contenu & mots-clés SEO
      │
      ▼
 StructureAgent → arborescence du site (pages, sections)
      │
      ▼
 ContentAgent → rédaction page par page
      │
      ▼
 DesignGeneratorAgent → charte graphique JSON
      │
      ▼
 WireframeAgent → wireframes HTML/CSS
      │
      ▼
 QAAgent → vérification qualité & cohérence
      │
      ▼
 SiteGenAgent → code HTML/CSS/JS final
```

---

## 👨‍💻 Auteur

Mohamed Blouza -- Projet réalisé dans le cadre d'un **Projet de Fin d'Études (PFE)**.

---
