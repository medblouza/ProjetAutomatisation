import base64
import json
import tempfile
import os

from colorthief import ColorThief
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

VISION_MODEL = "qwen/qwen3.6-27b"


# ============================================================
# COLOR EXTRACTION
# ============================================================

def extract_colors(
    image_bytes: bytes,
    media_type: str = "image/png"
) -> list[str]:
    """
    Extrait les couleurs dominantes avec ColorThief.
    """

    extension = ".png"

    if media_type == "image/jpeg":
        extension = ".jpg"

    elif media_type == "image/webp":
        extension = ".webp"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension
    ) as tmp:

        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:

        ct = ColorThief(tmp_path)

        palette = ct.get_palette(
            color_count=5,
            quality=1
        )

        return [
            f"#{r:02x}{g:02x}{b:02x}"
            for r, g, b in palette
        ]

    finally:

        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ============================================================
# JSON PARSER
# ============================================================

def parse_json_response(raw: str) -> dict:
    """
    Nettoie et parse la réponse du modèle.

    Gère notamment :
    - <think>...</think>
    - ```json ... ```
    - texte avant/après le JSON
    """

    if not raw:

        raise ValueError(
            "Le modèle a retourné une réponse vide."
        )

    raw = raw.strip()

    print("\n========== GROQ RAW RESPONSE ==========")
    print(repr(raw))
    print("========================================\n")

    # --------------------------------------------------------
    # 1. Supprimer le raisonnement <think>...</think>
    # --------------------------------------------------------

    if "<think>" in raw:

        think_start = raw.find("<think>")
        think_end = raw.find("</think>")

        if think_end != -1:

            raw = (
                raw[:think_start]
                + raw[think_end + len("</think>"):]
            )

        else:
            # Le modèle a commencé <think> mais n'a pas fermé.
            # Tout ce qui suit est probablement du raisonnement.
            raw = raw[:think_start]

    raw = raw.strip()

    # --------------------------------------------------------
    # 2. Supprimer markdown
    # --------------------------------------------------------

    raw = raw.replace(
        "```json",
        ""
    )

    raw = raw.replace(
        "```JSON",
        ""
    )

    raw = raw.replace(
        "```",
        ""
    )

    raw = raw.strip()

    # --------------------------------------------------------
    # 3. JSON direct
    # --------------------------------------------------------

    try:

        result = json.loads(raw)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # 4. Chercher {...}
    # --------------------------------------------------------

    start = raw.find("{")
    end = raw.rfind("}")

    if start != -1 and end != -1 and end > start:

        candidate = raw[start:end + 1]

        try:

            result = json.loads(candidate)

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            pass

    # --------------------------------------------------------
    # 5. Debug
    # --------------------------------------------------------

    print(
        "\n========== INVALID JSON RESPONSE =========="
    )

    print(raw)

    print(
        "===========================================\n"
    )

    raise ValueError(
        "Le modèle a retourné un contenu qui "
        "n'est pas un JSON valide."
    )


# ============================================================
# STYLE ANALYSIS
# ============================================================

def analyze_style_with_groq(
    image_bytes: bytes,
    media_type: str = "image/png"
) -> dict:
    """
    Analyse le style visuel d'une image avec
    Qwen 3.6 27B Vision.
    """

    # --------------------------------------------------------
    # Base64
    # --------------------------------------------------------

    b64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    data_url = (
        f"data:{media_type};base64,{b64}"
    )

    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    prompt = """
Analyze ONLY the visual design of this UI screenshot.

Do NOT explain your reasoning.

Do NOT describe the page content.

Do NOT describe products, services, text meaning,
business information, or functionality.

We only need these visual properties:

- typography style
- typography weight
- typography contrast
- interface density
- visual style
- visual mood

Return ONLY one JSON object.

Do NOT use <think>.
Do NOT write an explanation.
Do NOT use markdown.
Do NOT use code fences.
Do NOT write anything before or after the JSON.

Use exactly these fields:

{
  "typography_style": "mixed",
  "typography_weight": "regular",
  "typography_contrast": "medium",
  "density": "balanced",
  "visual_style": "elegant",
  "dominant_mood": "modern elegant interface"
}

Allowed values:

typography_style:
"serif"
"sans-serif"
"mixed"

typography_weight:
"light"
"regular"
"bold"
"mixed"

typography_contrast:
"low"
"medium"
"high"

density:
"compact"
"balanced"
"airy"

visual_style:
"minimal"
"corporate"
"playful"
"elegant"
"technical"

dominant_mood:
maximum 6 words.

OUTPUT ONLY JSON.
"""

    # --------------------------------------------------------
    # Groq request
    # --------------------------------------------------------

    try:

        response = client.chat.completions.create(

            model=VISION_MODEL,

            messages=[
                {
                    "role": "user",

                    "content": [

                        {
                            "type": "image_url",

                            "image_url": {
                                "url": data_url
                            }
                        },

                        {
                            "type": "text",
                            "text": prompt
                        }

                    ]
                }
            ],

            max_tokens=200,

            temperature=0,

            # IMPORTANT :
            # empêche le modèle de produire
            # une longue réponse <think>
            reasoning_effort="none"
        )

    except Exception as e:

        raise RuntimeError(
            f"Erreur lors de l'appel Groq Vision : {str(e)}"
        ) from e

    # --------------------------------------------------------
    # Get content
    # --------------------------------------------------------

    try:

        raw = response.choices[0].message.content

    except Exception as e:

        raise RuntimeError(
            "Impossible de récupérer la réponse de Groq."
        ) from e

    # --------------------------------------------------------
    # Parse
    # --------------------------------------------------------

    result = parse_json_response(raw)

    # --------------------------------------------------------
    # Normalize result
    # --------------------------------------------------------

    return {
        "typography": {

            "style": result.get(
                "typography_style",
                "sans-serif"
            ),

            "weight": result.get(
                "typography_weight",
                "regular"
            ),

            "contrast": result.get(
                "typography_contrast",
                "medium"
            )
        },

        "density": result.get(
            "density",
            "balanced"
        ),

        "visual_style": result.get(
            "visual_style",
            "minimal"
        ),

        "dominant_mood": result.get(
            "dominant_mood",
            ""
        )
    }


# ============================================================
# MERGE STYLES
# ============================================================

def merge_styles(
    results: list[dict]
) -> dict:
    """
    Fusionne les analyses de plusieurs images.
    """

    if not results:

        return {
            "palette": [],

            "density": "balanced",

            "typography": {
                "style": "sans-serif",
                "weight": "regular",
                "contrast": "medium"
            },

            "visual_style": "minimal",

            "dominant_mood": "",

            "refs_count": 0,

            "styles_per_ref": []
        }

    all_colors = []

    densities = []

    typo_styles = []
    typo_weights = []
    typo_contrasts = []

    visual_styles = []

    moods = []

    # --------------------------------------------------------
    # Collect
    # --------------------------------------------------------

    for result in results:

        all_colors.extend(
            result.get(
                "colors",
                []
            )
        )

        densities.append(
            result.get(
                "density",
                "balanced"
            )
        )

        typography = result.get(
            "typography",
            {}
        )

        typo_styles.append(
            typography.get(
                "style",
                "sans-serif"
            )
        )

        typo_weights.append(
            typography.get(
                "weight",
                "regular"
            )
        )

        typo_contrasts.append(
            typography.get(
                "contrast",
                "medium"
            )
        )

        visual_styles.append(
            result.get(
                "visual_style",
                "minimal"
            )
        )

        mood = result.get(
            "dominant_mood",
            ""
        )

        if mood:
            moods.append(mood)

    # --------------------------------------------------------
    # Unique colors
    # --------------------------------------------------------

    unique_colors = []

    seen = set()

    for color in all_colors:

        color = color.lower()

        if color not in seen:

            seen.add(color)

            unique_colors.append(color)

    # --------------------------------------------------------
    # Majority
    # --------------------------------------------------------

    def majority(
        values: list,
        default
    ):

        if not values:
            return default

        counts = {}

        for value in values:

            counts[value] = (
                counts.get(value, 0) + 1
            )

        return max(
            counts,
            key=counts.get
        )

    # --------------------------------------------------------
    # Final style
    # --------------------------------------------------------

    return {

        "palette": unique_colors[:6],

        "density": majority(
            densities,
            "balanced"
        ),

        "typography": {

            "style": majority(
                typo_styles,
                "sans-serif"
            ),

            "weight": majority(
                typo_weights,
                "regular"
            ),

            "contrast": majority(
                typo_contrasts,
                "medium"
            )
        },

        "visual_style": majority(
            visual_styles,
            "minimal"
        ),

        "dominant_mood": (
            moods[0]
            if moods
            else ""
        ),

        "refs_count": len(results),

        "styles_per_ref": results
    }


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def extract_style_from_images(
    images: list[tuple[bytes, str]]
) -> dict:
    """
    Point d'entrée principal.

    images:
        [
            (image_bytes, media_type),
            (image_bytes, media_type)
        ]
    """

    if not images:

        raise ValueError(
            "Aucune image n'a été fournie."
        )

    results = []

    # --------------------------------------------------------
    # Analyze each image
    # --------------------------------------------------------

    for index, (
        image_bytes,
        media_type
    ) in enumerate(
        images,
        start=1
    ):

        print(
            f"\n===== Analyse image "
            f"{index}/{len(images)} ====="
        )

        if not image_bytes:

            raise ValueError(
                f"L'image {index} est vide."
            )

        # ----------------------------------------------------
        # Color extraction
        # ----------------------------------------------------

        try:

            colors = extract_colors(
                image_bytes,
                media_type
            )

        except Exception as e:

            raise RuntimeError(
                f"Erreur extraction couleurs "
                f"image {index} : {str(e)}"
            ) from e

        # ----------------------------------------------------
        # AI style analysis
        # ----------------------------------------------------

        try:

            style = analyze_style_with_groq(
                image_bytes,
                media_type
            )

        except Exception as e:

            raise RuntimeError(
                f"Erreur analyse style "
                f"image {index} : {str(e)}"
            ) from e

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        results.append({
            "colors": colors,
            **style
        })

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    final_style = merge_styles(
        results
    )

    # --------------------------------------------------------
    # Debug
    # --------------------------------------------------------

    print(
        "\n========== FINAL STYLE =========="
    )

    print(
        json.dumps(
            final_style,
            indent=2,
            ensure_ascii=False
        )
    )

    print(
        "=================================\n"
    )

    return final_style