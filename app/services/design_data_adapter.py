# app/services/design_data_adapter.py
from app.cleaner import clean_dp_data

def adapt_for_design(raw_dp_data: dict, client_code: str) -> dict:
    """
    raw_dp_data : sortie brute de DpService.get_info_by_code()
    Retourne un dict propre pour DesignGeneratorAgent.run()
    """
    cleaned = clean_dp_data(raw_dp_data)

    # Couleurs : filtre les None qui viennent de clean_dp_data
    branding = cleaned.get("branding") or {}
    colors = [c for c in branding.get("colors", []) if c]

    # Pages : noms uniquement pour guider le LLM
    page_names = [
        p["name"] for p in cleaned.get("pages", [])
        if p.get("name")
    ]
    if not page_names:
        page_names = ["Accueil", "Services", "Contact"]

    return {
        "id":          client_code,
        "name":        cleaned.get("company_name") or "Client",
        "sector":      cleaned.get("activity") or "",
        "description": cleaned.get("company_details") or cleaned.get("experience") or "",
        "city":        cleaned.get("city") or "",
        "pages":       page_names,
        "colors":      colors,
        "services":    cleaned.get("services") or [],
        "keywords":    cleaned.get("keywords") or [],
    }