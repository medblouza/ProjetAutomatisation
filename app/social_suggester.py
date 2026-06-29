import requests
from bs4 import BeautifulSoup

# ─────────────────────────────
# 1. Build queries (multi-queries)
# ─────────────────────────────
def build_queries(data):

    name = data.get("company_name", "")
    city = data.get("city", "")
    activity = data.get("activity", "")
    services = " ".join(data.get("services", [])[:3])

    return [
        f"{name} {city} facebook",
        f"{name} {city} instagram",
        f"{name} {activity} {city} facebook",
        f"{name} {services} {city}"
    ]


# ─────────────────────────────
# 2. Search Google (simple scraping)
# ─────────────────────────────
def search_links(query):

    headers = {"User-Agent": "Mozilla/5.0"}

    url = f"https://www.google.com/search?q={query}"
    res = requests.get(url, headers=headers)

    soup = BeautifulSoup(res.text, "html.parser")

    links = []

    for a in soup.select("a"):
        href = a.get("href")

        if not href:
            continue

        # nettoyage lien Google
        if "/url?q=" in href:
            link = href.split("/url?q=")[1].split("&")[0]

            if "facebook.com" in link or "instagram.com" in link:
                links.append(link)

    return links


# ─────────────────────────────
# 3. Score des liens
# ─────────────────────────────
def score_links(links, data):

    name = (data.get("company_name") or "").lower().replace(" ", "")
    city = (data.get("city") or "").lower()

    scored = []

    for link in links:
        score = 0
        l = link.lower()

        if name and name in l:
            score += 2

        if city and city in l:
            score += 1

        if "facebook.com" in l or "instagram.com" in l:
            score += 1

        scored.append((link, score))

    # tri par score
    scored.sort(key=lambda x: x[1], reverse=True)

    return [l[0] for l in scored]


# ─────────────────────────────
# 4. Fonction principale
# ─────────────────────────────
def suggest_social(data):

    queries = build_queries(data)

    all_links = []

    for q in queries:
        links = search_links(q)
        all_links.extend(links)

    # supprimer doublons
    all_links = list(set(all_links))

    ranked = score_links(all_links, data)

    return {
        "facebook": [l for l in ranked if "facebook.com" in l][:3],
        "instagram": [l for l in ranked if "instagram.com" in l][:3]
    }