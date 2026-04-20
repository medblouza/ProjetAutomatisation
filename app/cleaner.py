import re

def clean_text(text):
    if not text:
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_services(text):
    if not text:
        return []
    return [clean_text(s) for s in re.split(r",|\n|-", text) if s.strip()]

def extract_pages(details):
    pages = []
    sites = details.get("sites", [])

    if not sites:
        return pages

    for p in sites[0].get("siteTrees", []):
        pages.append({
            "name": clean_text(p.get("name")),
            "content": clean_text(p.get("description"))
        })

    return pages


def extract_social(details):
    social = {}
    for s in details.get("socialNetworks", []):
        social[s.get("name").lower()] = s.get("url")
    return social


def clean_dp_data(raw):
    details = raw.get("details", {})
    company = raw.get("company", {})

    if isinstance(details, list):
        details = details[0] if details else {}

    return {
        # Entreprise
        "company_name": company.get("Name"),
        "activity": company.get("Industry"),
        "city": details.get("mainLocality"),

        # Business
        "target": details.get("customers"),
        "services": extract_services(details.get("serviceDetails")),
        "strengths": clean_text(details.get("keyPoints")),
        "competitor": clean_text(details.get("competitor")),

        # Story
        "experience": clean_text(details.get("experience")),
        "company_details": clean_text(details.get("companyDetails")),

        # Zone
        "zone": clean_text(details.get("geographicalArea")),

        # Digital
        "social": extract_social(details),
        "keywords": details.get("sites", [{}])[0].get("seoKeywords", []),

        # Pages
        "pages": extract_pages(details),

        # Branding
        "branding": {
            "colors": [
                details.get("sites", [{}])[0].get("mainColor"),
                details.get("sites", [{}])[0].get("secondaryColor"),
            ],
            "style": details.get("sites", [{}])[0].get("siteStyles", [])
        }
    }