import time
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Any
import requests


# ─── Constants ───────────────────────────────────────────────────────────────
LOGIN_URL    = "https://dp.localetmoi.fr/localfr-api/generate-user-token"
PARTNER_URL  = "https://api.local.fr/api/partners?customerCode={code}&properties[]=id"
DETAILS_URL  = "https://api.local.fr{partner_id}"
COMPANY_URL  = "https://dp.localetmoi.fr/api/salesforce/account/{code}"

PAGES_ORPHELINES = [
    "nos références", "nos réalisations", "nos partenaires", "nos actualités",
    "mes réalisations", "mes realisations", "mes partenaires",
    "mes chantiers en photo", "livre d'or", "galerie photos", "galerie photo",
    "galerie photos et video", "galerie", "devenez partenaires", "blog",
    "actualités", "actualité", "devis gratuit", "demande de devis",
    "zones d'intervention", "avis clients", "portofolio", "photo",
    "réalisations", "realisations", "nos réalisation", "événementiel",
    "témoignages",
]

PAGES_CONTACT = [
    "contact / devis", "Contact - Devis", "contact - devis", "contact",
    "contact & devis", "contact / inscription", "contact/inscription",
    "contact et accès", "contact et acces", "contact et devis",
    "contact et réservation", "contactez-nous", "contactez-moi",
    "formulaire de contact", "contact/devis", "contact-devis",
    "contact / devis gratuit", "contact/devis gratuit", "nous contacter",
    "contacts", "prise de rdv / contact", "prise de rdv/contact",
    "avis-contact",
]

# ─── Data structures ──────────────────────────────────────────────────────────
@dataclass
class ServiceResult:
    is_success: bool
    data: Any = None
    message: str = ""

    @classmethod
    def success(cls, data):
        return cls(is_success=True, data=data)

    @classmethod
    def failure(cls, message):
        return cls(is_success=False, message=message)


@dataclass
class Variable:
    id: int
    name: str
    param: str
    value: str = ""
    value_original: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)


# ─── Helper utilities ─────────────────────────────────────────────────────────
def _get(obj: dict, path: str, default: str = "") -> str:
    """Dot-notation accessor with fallback."""
    if obj is None:
        return default
    parts = path.split(".")
    cur = obj
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return str(cur) if cur is not None else default


def _jget(data, *keys, default=""):
    """Safe nested dict access."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
            if data is None:
                return default
        elif isinstance(data, list) and isinstance(key, int):
            try:
                data = data[key]
            except IndexError:
                return default
        else:
            return default
    return str(data) if data is not None else default


# ─── Main Service ─────────────────────────────────────────────────────────────
class DpService:
    def __init__(self, username: str = "", password: str = ""):
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = False   # mirrors "InsecureClient" in C#
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # ── Auth ──────────────────────────────────────────────────────────────────
    def login(self) -> bool:
        if self.token:
            return True
        try:
            resp = self.session.post(
                LOGIN_URL,
                json={"username": self.username, "password": self.password},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if "access_token" in data:
                self.token = data["access_token"]
                return True
            return False
        except Exception:
            self.token = None
            return False

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _get_request(self, url: str) -> requests.Response:
        resp = self.session.get(url, headers=self._headers(), timeout=30)
        if resp.status_code == 401:
            self.token = None
            if self.login():
                resp = self.session.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp

    # ── get_info_by_code ──────────────────────────────────────────────────────
    def get_info_by_code(self, code: str) -> ServiceResult:
        if not self.login():
            return ServiceResult.failure("Échec de l'authentification.")
        try:
            # 1 — Partner lookup
            partner_url = PARTNER_URL.replace("{code}", urllib.parse.quote(code))
            partner_resp = self._get_request(partner_url)
            partner_data = partner_resp.json()

            partner_id = None
            if isinstance(partner_data, dict):
                members = partner_data.get("hydra:member", [])
                if members:
                    partner_id = members[0].get("@id")
            elif isinstance(partner_data, list) and partner_data:
                first = partner_data[0]
                partner_id = first.get("@id") or first.get("id")
                if partner_id and not str(partner_id).startswith("/"):
                    partner_id = f"/api/partners/{partner_id}"

            if not partner_id:
                return ServiceResult.failure("Partner ID introuvable.")

            # 2 — Partner details
            details_url = DETAILS_URL.replace("{partner_id}", partner_id)
            details_resp = self._get_request(details_url)
            details_data = details_resp.json()

            if isinstance(details_data, list):
                if not details_data:
                    return ServiceResult.failure("Détails vides.")
                details = details_data[0]
            else:
                details = details_data

            company_code = details.get("company") if isinstance(details, dict) else None
            if not company_code:
                return ServiceResult.failure("Code company introuvable.")

            # 3 — Salesforce company
            company_url = COMPANY_URL.replace("{code}", urllib.parse.quote(str(company_code)))
            company_resp = self._get_request(company_url)
            company_data = company_resp.json()

            return ServiceResult.success({
                "partner": partner_data,
                "details": details_data if isinstance(details_data, list) else details,
                "company": company_data,
            })

        except requests.HTTPError as e:
            return ServiceResult.failure(f"HTTP {e.response.status_code}: {str(e)}")
        except Exception as e:
            return ServiceResult.failure(str(e))

    # ── process_codesage ──────────────────────────────────────────────────────
    def process_codesage(self, code_sage: str) -> ServiceResult:
        info_result = self.get_info_by_code(code_sage)
        if not info_result.is_success:
            return ServiceResult.failure(info_result.message)

        try:
            raw = info_result.data
            details = raw.get("details") or {}
            company = raw.get("company") or {}

            # Normalise details (list or dict)
            if isinstance(details, list):
                details = details[0] if details else {}

            dp_data = self._extract_dp_data(details, company)

            variables = self._get_default_variables()
            updated_vars = []
            for v in variables:
                original = self._extract_value(v, dp_data)
                v.value = v.value or original
                v.value_original = v.value_original or original
                updated_vars.append(v)

            # Filter template placeholders
            updated_vars = [
                v for v in updated_vars
                if not self._is_internal_var(v.param, v.name)
                and not self._is_sous_page_var(v.param, v.name)
            ]

            base_id = int(time.time() * 1000)
            offset = [0]

            def next_id():
                i = base_id + offset[0]
                offset[0] += 1
                return i

            dyn_vars: List[Variable] = []

            # Internal pages
            for i, page in enumerate(dp_data.get("internalPages", []), 1):
                dyn_vars += [
                    Variable(next_id(), f"Nom de page interne {i}", f"param{{nom_page_interne_{i}}}", page.get("name",""), page.get("name",""), {"source":"dp-internal"}),
                    Variable(next_id(), f"Contenu de page interne {i}", f"param{{contenu_page_interne_{i}}}", page.get("content",""), page.get("content",""), {"source":"dp-internal"}),
                ]

            # Orpheline pages
            for i, page in enumerate(dp_data.get("orphelinePages", []), 1):
                dyn_vars += [
                    Variable(next_id(), f"Nom de page orpheline {i}", f"param{{nom_page_orpheline_{i}}}", page.get("name",""), page.get("name",""), {"source":"dp-orpheline"}),
                    Variable(next_id(), f"Contenu de page orpheline {i}", f"param{{contenu_page_orpheline_{i}}}", page.get("content",""), page.get("content",""), {"source":"dp-orpheline"}),
                ]

            # Sous-pages
            for i, page in enumerate(dp_data.get("sousPages", []), 1):
                dyn_vars += [
                    Variable(next_id(), f"Nom de page sous-page {i}", f"param{{nom_page_sous_page_{i}}}", page.get("name",""), page.get("name",""), {"source":"dp-souspage"}),
                    Variable(next_id(), f"Contenu de page sous-page {i}", f"param{{contenu_page_sous_page_{i}}}", page.get("content",""), page.get("content",""), {"source":"dp-souspage"}),
                ]

            # Shop products
            for i, prod in enumerate(dp_data.get("shopProducts", []), 1):
                dyn_vars += [
                    Variable(next_id(), f"Titre du produit {i}", f"param{{product_name_{i}}}", prod.get("productName",""), prod.get("productName",""), {"source":"dp-product"}),
                    Variable(next_id(), f"Catégorie du produit {i}", f"param{{product_category_{i}}}", prod.get("categories",""), prod.get("categories",""), {"source":"dp-product"}),
                    Variable(next_id(), f"Sous-catégorie du produit {i}", f"param{{product_subcategory_{i}}}", prod.get("subCategories",""), prod.get("subCategories",""), {"source":"dp-product"}),
                    Variable(next_id(), f"Description du produit {i}", f"param{{product_description_{i}}}", prod.get("description",""), prod.get("description",""), {"source":"dp-product"}),
                ]

            all_vars = updated_vars + dyn_vars
            result_dict = {
                v.param.replace("param{", "").replace("}", ""): v.value
                for v in all_vars
                if v.param and v.value
            }
            return ServiceResult.success(result_dict)

        except Exception as e:
            return ServiceResult.failure(str(e))

    # ── Data extraction helpers ───────────────────────────────────────────────
    def _extract_dp_data(self, details: dict, company: dict) -> dict:
        extraction = self._extract_pages(details)

        shop_products = self._extract_shop_products(details)
        first_prod = shop_products[0] if shop_products else {}

        secs = self._get_secondary_localities(details, company)
        sec1 = secs[0] if len(secs) > 0 else _get(details, "localiteSecondaire1") or _get(company, "localiteSecondaire1")
        sec2 = secs[1] if len(secs) > 1 else _get(details, "localiteSecondaire2") or _get(company, "localiteSecondaire2")

        def coalesce(d_key, c_key=None):
            v = _get(details, d_key)
            if v:
                return v
            return _get(company, c_key or d_key)

        return {
            "activity": _get(company, "Industry"),
            "name": _get(company, "Name"),
            "mainLocality": _get(details, "mainLocality"),
            "contactPageName": self._extract_contact_page_name(details),
            "contactPageContent": self._extract_contact_page_content(details),
            "code_ape": _get(company, "Libell_code_APE__c"),
            "pronoun": coalesce("pronoun"),
            "companyDetails": coalesce("companyDetails"),
            "customers": coalesce("customers"),
            "keyPoints": coalesce("keyPoints"),
            "competitor": coalesce("competitor"),
            "keywords": self._extract_keywords(details),
            "internalPages": extraction["internal"],
            "orphelinePages": extraction["orphelines"],
            "sousPages": extraction["sousPages"],
            "openingRanges": self._extract_opening_ranges(details),
            "aboutOpeningRange": _get(details, "aboutOpeningRange"),
            "instagramUrl": self._extract_social(details, "instagram"),
            "facebookUrl": self._extract_social(details, "facebook"),
            "localiteCommune": _get(company, "BillingCity"),
            "secondaryLocalities": ", ".join(secs),
            "coverageArea": self._extract_coverage_area(details),
            "isAlone": _get(details, "isAlone"),
            "partners": _get(details, "partners"),
            "experience": _get(details, "experience"),
            "serviceDetails": _get(details, "serviceDetails"),
            "goalsStore": _get(details, "goalsStore"),
            "productBrands": _get(details, "productBrands"),
            "homePageName": self._extract_home_page_name(details),
            "homePageContent": self._extract_home_page_content(details),
            "shopProducts": shop_products,
            "product_name": first_prod.get("productName", ""),
            "product_category": first_prod.get("categories", ""),
            "product_subcategory": first_prod.get("subCategories", ""),
            "product_description": first_prod.get("description", ""),
            "localiteSecondaire1": sec1,
            "localiteSecondaire2": sec2,
        }

    def _extract_pages(self, details: dict) -> dict:
        internal, orphelines, sous_pages = [], [], []
        sites = details.get("sites") if isinstance(details, dict) else None
        if not sites or not isinstance(sites, list) or not sites:
            return {"internal": internal, "orphelines": orphelines, "sousPages": sous_pages}

        first_site = sites[0]
        site_trees = first_site.get("siteTrees") or []
        if not site_trees:
            return {"internal": internal, "orphelines": orphelines, "sousPages": sous_pages}

        sorted_pages = sorted(site_trees, key=lambda x: x.get("position") or 0)
        orphelines_lower = {p.lower().strip() for p in PAGES_ORPHELINES}
        contact_lower = {p.lower().strip() for p in PAGES_CONTACT}

        # Build orphan sets
        orphan_root: set = set()
        orphan_with_children: set = set()
        home_page = self._identify_home_page(sorted_pages)
        home_name = (home_page.get("name") or "").lower().strip() if home_page else ""

        for page in sorted_pages:
            name_lower = (page.get("name") or "").lower().strip()
            if name_lower in orphelines_lower:
                orphan_root.add(name_lower)
                orphan_with_children.add(name_lower)
                for child in page.get("children") or []:
                    cname = (child.get("name") or "").lower().strip()
                    if cname:
                        orphan_with_children.add(cname)

        # Propagate orphan status via parent
        for page in sorted_pages:
            parent = page.get("parent")
            if parent and parent.get("name"):
                pname = parent["name"].lower().strip()
                name_lower = (page.get("name") or "").lower().strip()
                if pname in orphan_with_children and name_lower not in orphan_with_children:
                    orphan_with_children.add(name_lower)

        added: set = set()
        valid_parents = []

        for page in sorted_pages:
            position = page.get("position") or 0
            name = (page.get("name") or "").strip()
            name_lower = name.lower()
            has_parent = bool(page.get("parent") and page["parent"].get("name"))
            is_orpheline = name_lower in orphan_with_children
            is_orpheline_root = name_lower in orphan_root
            is_contact = name_lower in contact_lower
            is_home = name_lower == home_name

            if is_orpheline_root and not is_home:
                if name not in added:
                    orphelines.append({"name": name, "content": page.get("description") or "", "isOrpheline": True})
                    added.add(name)
            elif is_orpheline and has_parent and not is_home and not is_contact:
                parent_name = (page.get("parent") or {}).get("name", "")
                if name:
                    sous_pages.append({"name": name, "content": page.get("description") or "", "parentName": parent_name})
                    added.add(name)
            elif not is_contact and not is_home and not has_parent and position != 0:
                valid_parents.append(page)

        for page in sorted(valid_parents, key=lambda x: x.get("position") or 0):
            name = (page.get("name") or "").strip()
            content = page.get("description") or ""
            children_arr = []

            for child in sorted(page.get("children") or [], key=lambda x: x.get("position") or 0):
                cname = (child.get("name") or "").strip()
                cname_lower = cname.lower()
                if cname_lower not in orphan_with_children and cname_lower not in contact_lower and cname_lower != home_name:
                    ccontent = child.get("description") or ""
                    children_arr.append({"name": cname, "content": ccontent})
                    content += f" , \n {cname} " + (ccontent if ccontent else "")
                    sous_pages.append({"name": cname, "content": ccontent, "parentName": name})

            internal.append({"name": name, "content": content, "children": children_arr})
            added.add(name)

        return {"internal": internal, "orphelines": orphelines, "sousPages": sous_pages}

    def _identify_home_page(self, pages: list) -> Optional[dict]:
        for p in pages:
            if (p.get("position") or -1) == 0 and not p.get("parent"):
                return p
        for p in pages:
            name = (p.get("name") or "").lower().strip()
            if name in ("accueil", "home"):
                return p
        for p in pages:
            if not p.get("parent"):
                return p
        return None

    def _extract_contact_page_name(self, details: dict) -> str:
        contact_lower = {c.lower() for c in PAGES_CONTACT}
        sites = details.get("sites") if isinstance(details, dict) else []
        if sites:
            for p in (sites[0].get("siteTrees") or []):
                if (p.get("name") or "").lower() in contact_lower:
                    return p.get("name", "")
        return ""

    def _extract_contact_page_content(self, details: dict) -> str:
        contact_lower = {c.lower() for c in PAGES_CONTACT}
        sites = details.get("sites") if isinstance(details, dict) else []
        if sites:
            for p in (sites[0].get("siteTrees") or []):
                if (p.get("name") or "").lower() in contact_lower:
                    return p.get("description") or ""
        return ""

    def _extract_keywords(self, details: dict) -> str:
        sites = details.get("sites") if isinstance(details, dict) else []
        if sites:
            kws = sites[0].get("seoKeywords") or []
            return " , ".join(str(k) for k in kws[:10])
        return ""

    def _extract_shop_products(self, details: dict) -> list:
        if not isinstance(details, dict):
            return []
        products = (details.get("partnerBoutique") or {}).get("shopProducts") or []
        return [
            {
                "productName": p.get("productName", ""),
                "categories": p.get("categories", ""),
                "subCategories": p.get("subCategories", ""),
                "description": p.get("description", ""),
            }
            for p in products
        ]

    def _extract_opening_ranges(self, details: dict) -> list:
        ranges = details.get("openingRanges") or [] if isinstance(details, dict) else []
        return [r for r in ranges if r.get("isOpeningRange") and not r.get("isCampaign")]

    def _extract_social(self, details: dict, network: str) -> str:
        social = details.get("socialNetworks") or [] if isinstance(details, dict) else []
        for s in social:
            if (s.get("name") or "").lower() == network.lower():
                return s.get("url") or ""
        return ""

    def _get_secondary_localities(self, details: dict, company: dict) -> list:
        locs = []
        for src in (details, company):
            val = src.get("secondaryLocalities") if isinstance(src, dict) else None
            if isinstance(val, list):
                locs += [str(i) for i in val]
            elif isinstance(val, str) and val:
                locs += [s.strip() for s in re.split(r"[,;|]", val) if s.strip()]
            if len(locs) >= 2:
                break
        return locs[:2]

    def _extract_coverage_area(self, details: dict) -> str:
        sites = details.get("sites") if isinstance(details, dict) else []
        if sites:
            return sites[0].get("coverageArea") or ""
        return ""

    def _extract_home_page_name(self, details: dict) -> str:
        sites = details.get("sites") if isinstance(details, dict) else []
        if sites:
            pages = sites[0].get("siteTrees") or []
            p = self._identify_home_page(pages)
            return (p.get("name") or "") if p else ""
        return ""

    def _extract_home_page_content(self, details: dict) -> str:
        sites = details.get("sites") if isinstance(details, dict) else []
        if sites:
            pages = sites[0].get("siteTrees") or []
            p = self._identify_home_page(pages)
            return (p.get("description") or "") if p else ""
        return ""

    # ── Variable extraction ───────────────────────────────────────────────────
    def _extract_value(self, v: Variable, dp: dict) -> str:
        g = lambda k: dp.get(k) or ""
        name = v.name

        mapping = {
            "Secteur d'activité": g("activity"),
            "Secteur activite": g("activity"),
            "Enseigne": g("name"),
            "Adresse": g("address"),
            "Localité principale": g("mainLocality"),
            "Localité commune": g("localiteCommune"),
            "Nom de page contact": g("contactPageName"),
            "Contenu de page contact": g("contactPageContent"),
            "Localité secondaire 1": g("localiteSecondaire1"),
            "Localité secondaire 2": g("localiteSecondaire2"),
            "Code APE": g("code_ape"),
            "Mots clés": g("keywords"),
            "Avec quel pronom devons-nous rédiger votre site ?": g("pronoun"),
            "Détails de l'entreprise": g("companyDetails"),
            "Quelle est votre typologie client ?": g("customers"),
            "Points clés": g("keyPoints"),
            "Qu'est-ce qui vous distingue des concurrents ?": g("competitor"),
            "Nom de page accueil": g("homePageName"),
            "Contenu de page accueil": g("homePageContent"),
            "Travaillez-vous seul(e) ou en équipe": self._format_alone(dp.get("isAlone")),
            "Avec quelles marques travaillez-vous ?": g("partners"),
            "Vos expériences": g("experience"),
            "Prestations détaillées": g("serviceDetails"),
            "Concepts et objectifs de la boutique": g("goalsStore"),
            "Type de produits et marques proposées": g("productBrands"),
            "Zone d'intervention": " ".join(filter(None, [g("coverageArea"), g("mainLocality")])),
            "Facebook": g("facebookUrl"),
            "Instagram": g("instagramUrl"),
            "Horaires exceptionnels avec les remarques": g("aboutOpeningRange"),
            "Horaires habituels": self._format_horaires(dp.get("openingRanges") or []),
            "Titre du produit": g("product_name"),
            "Catégorie du produit": g("product_category"),
            "Sous-catégorie du produit": g("product_subcategory"),
            "Description du produit": g("product_description"),
        }
        return mapping.get(name, "")

    def _format_alone(self, val) -> str:
        if val is None:
            return ""
        s = str(val).lower()
        if s in ("true", "1"):
            return "Seul(e)"
        if s in ("false", "0"):
            return "En équipe"
        return ""

    def _format_horaires(self, ranges: list) -> str:
        valid = [r for r in ranges if r.get("isOpeningRange") and not r.get("isCampaign")]
        valid.sort(key=lambda r: (r.get("dayOfWeek") or 0, r.get("startTime") or 0))

        by_day: dict = {}
        for r in valid:
            day = r.get("dayOfWeek") or 0
            horaire = f"{self._fmt_time(r.get('startTime',0))} - {self._fmt_time(r.get('endTime',0))}"
            by_day.setdefault(day, [])
            if horaire not in by_day[day]:
                by_day[day].append(horaire)

        # Group days by same schedule
        schedule_days: dict = {}
        for day, horaires in by_day.items():
            key = " et ".join(horaires)
            schedule_days.setdefault(key, [])
            schedule_days[key].append(day)

        days_fr = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
        lines = []
        for horaire_str, days in schedule_days.items():
            days.sort()
            days_text = ", ".join(days_fr[d] if 0 <= d < len(days_fr) else f"Jour {d}" for d in days)
            lines.append(f"{days_text} : {horaire_str}")
        return "\n".join(lines)

    def _fmt_time(self, seconds: int) -> str:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h:02d}h{m:02d}"

    # ── Filters ───────────────────────────────────────────────────────────────
    def _is_internal_var(self, param: str, name: str) -> bool:
        p, n = (param or "").lower(), (name or "").lower()
        return p in ("param{nom_page_interne}", "param{contenu_page_interne}") or \
               n in ("nom de page interne", "contenu de page interne")

    def _is_sous_page_var(self, param: str, name: str) -> bool:
        p, n = (param or "").lower(), (name or "").lower()
        return p in ("param{nom_page_sous_page}", "param{contenu_page_sous_page}") or \
               n in ("nom de page sous-page", "contenu de page sous-page")

    # ── Default variables list ────────────────────────────────────────────────
    def _get_default_variables(self) -> List[Variable]:
        defs = [
            (1,  "Secteur d'activité",                                "param{secteur_activite}"),
            (2,  "Mots clés",                                         "param{mots_cles}"),
            (3,  "Enseigne",                                          "param{enseigne}"),
            (4,  "Localité principale",                               "param{localite_principale}"),
            (5,  "Localité commune",                                  "param{localite_commune}"),
            (6,  "Localité secondaire 1",                             "param{localite_secondaire_1}"),
            (7,  "Localité secondaire 2",                             "param{localite_secondaire_2}"),
            (8,  "Horaires habituels",                                "param{horaire_habituels}"),
            (9,  "Horaires exceptionnels avec les remarques",         "param{horaire_exceptionnels}"),
            (10, "Facebook",                                          "param{facebook}"),
            (11, "Instagram",                                         "param{instagram}"),
            (12, "Zone d'intervention",                               "param{zone_intervention}"),
            (13, "Code APE",                                          "param{code_ape}"),
            (14, "Avec quel pronom devons-nous rédiger votre site ?", "param{pronom}"),
            (15, "Détails de l'entreprise",                          "param{details_entreprise}"),
            (16, "Quelle est votre typologie client ?",               "param{typologie_client}"),
            (17, "Points clés",                                       "param{points_cles}"),
            (18, "Qu'est-ce qui vous distingue des concurrents ?",    "param{distinction_concurrents}"),
            (19, "Nom de page accueil",                               "param{nom_page_accueil}"),
            (20, "Contenu de page accueil",                           "param{contenu_page_accueil}"),
            (21, "Nom de page interne",                               "param{nom_page_interne}"),
            (22, "Contenu de page interne",                           "param{contenu_page_interne}"),
            (23, "Nom de page orpheline",                             "param{nom_page_orpheline}"),
            (24, "Contenu de page orpheline",                         "param{contenu_page_orpheline}"),
            (241,"Nom de page sous-page",                             "param{nom_page_sous_page}"),
            (242,"Contenu de page sous-page",                         "param{contenu_page_sous_page}"),
            (25, "Nom de page contact",                               "param{nom_page_contact}"),
            (26, "Contenu de page contact",                           "param{contenu_page_contact}"),
            (27, "Travaillez-vous seul(e) ou en équipe",              "param{seul_equipe}"),
            (28, "Avec quelles marques travaillez-vous ?",            "param{partenaires_marques}"),
            (29, "Vos expériences",                                   "param{vos_experiences}"),
            (30, "Prestations détaillées",                            "param{prestations_detaillees}"),
            (31, "Concepts et objectifs de la boutique",              "param{concepts_objectifs}"),
            (32, "Type de produits et marques proposées",             "param{type_produits_marques}"),
            (33, "Titre du produit",                                  "param{product_name}"),
            (34, "Catégorie du produit",                              "param{product_category}"),
            (35, "Sous-catégorie du produit",                         "param{product_subcategory}"),
            (36, "Description du produit",                            "param{product_description}"),
        ]
        return [Variable(id=i, name=n, param=p) for i, n, p in defs]