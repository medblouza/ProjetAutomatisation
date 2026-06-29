import base64
import json
import tempfile
import os
from colorthief import ColorThief
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"



def extract_colors(image_bytes: bytes) -> list[str]:
    """Extrait la palette de couleurs dominantes via ColorThief."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        ct = ColorThief(tmp_path)
        palette = ct.get_palette(color_count=5, quality=1)
        return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette]
    finally:
        os.unlink(tmp_path)


def analyze_style_with_groq(image_bytes: bytes, media_type: str = "image/png") -> dict:
    """Analyse typo, densité et style visuel via Groq Llama 4 Vision."""
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{media_type};base64,{b64}"

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url},
                    },
                    {
                        "type": "text",
                        "text": """Analyse cette interface UI et retourne UNIQUEMENT un JSON valide, sans markdown ni backticks :
{
  "typography": {
    "style": "serif | sans-serif | mixed",
    "weight": "light | regular | bold | mixed",
    "contrast": "low | medium | high"
  },
  "density": "compact | balanced | airy",
  "visual_style": "minimal | corporate | playful | elegant | technical",
  "dominant_mood": "description courte (max 6 mots)"
}""",
                    },
                ],
            }
        ],
        max_tokens=500,
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def merge_styles(results: list[dict]) -> dict:
    """Fusionne les analyses de plusieurs images en un style cohérent."""
    all_colors = []
    densities = []
    typo_styles = []
    visual_styles = []
    moods = []

    for r in results:
        all_colors.extend(r.get("colors", []))
        densities.append(r.get("density", "balanced"))
        typo_styles.append(r.get("typography", {}).get("style", "sans-serif"))
        visual_styles.append(r.get("visual_style", "minimal"))
        moods.append(r.get("dominant_mood", ""))

    seen = set()
    unique_colors = []
    for c in all_colors:
        if c not in seen:
            seen.add(c)
            unique_colors.append(c)

    def majority(lst):
        return max(set(lst), key=lst.count)

    return {
        "palette": unique_colors[:6],
        "density": majority(densities),
        "typography": {
            "style": majority(typo_styles),
            "weight": results[0].get("typography", {}).get("weight", "regular"),
            "contrast": results[0].get("typography", {}).get("contrast", "medium"),
        },
        "visual_style": majority(visual_styles),
        "dominant_mood": moods[0] if moods else "",
        "refs_count": len(results),
        "styles_per_ref": results,
    }


def extract_style_from_images(images: list[tuple[bytes, str]]) -> dict:
    """
    Point d'entrée principal.
    images : liste de tuples (image_bytes, media_type)
    """
    results = []
    for image_bytes, media_type in images:
        colors = extract_colors(image_bytes)
        style = analyze_style_with_groq(image_bytes, media_type)
        results.append({"colors": colors, **style})

    return merge_styles(results)