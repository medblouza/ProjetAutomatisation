from __future__ import annotations

import os
from typing import Any, Dict

from google import genai
from google.genai import types

from app.schema.web_generator_schema import GeneratedSite


class WebCodeGenerator:

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        self.client = genai.Client(api_key=api_key)

    def generate(self, design_json: Dict[str, Any]) -> GeneratedSite:

        system_instruction = """
Tu es un développeur Web Senior spécialisé dans la transformation
de DesignJSON en sites web professionnels.

Le JSON fourni décrit complètement le design et la structure d'un site.

OBJECTIF :
Transformer exactement ce DesignJSON en un site HTML/CSS/JS fonctionnel.

RÈGLES IMPORTANTES :

1. Générer TOUTES les pages présentes dans :
   design_json.pages

2. Chaque page doit avoir son propre fichier HTML.

3. La page d'accueil DOIT être :
   index.html

4. Les autres pages doivent utiliser des noms de fichiers cohérents :
   services.html
   contact.html
   a-propos.html
   etc.

5. Tous les liens de navigation doivent fonctionner.

6. Les liens doivent être relatifs :
   href="index.html"
   href="services.html"
   href="contact.html"

7. Générer UN seul :
   style.css

8. Générer UN seul :
   script.js
   uniquement lorsque JavaScript est nécessaire.

9. Le design_system du JSON doit être respecté :
   - couleurs
   - typographie
   - tailles
   - spacing
   - radius
   - thème

10. Chaque composant doit être transformé en véritable HTML.
    Ne pas afficher le JSON directement.

11. Ne pas utiliser de framework externe.
    Le résultat doit fonctionner simplement en ouvrant index.html.

12. Le site doit être responsive :
    desktop
    tablet
    mobile

13. Ne jamais supprimer une page présente dans le JSON.

14. Ne jamais inventer une structure de navigation différente.

15. Les textes fournis dans le JSON doivent être utilisés comme contenu
    du site.

16. Si une image est référencée mais qu'aucun fichier image réel n'est
    fourni, créer un placeholder visuel propre plutôt qu'une image cassée.

17. Le résultat doit fonctionner hors ligne après extraction du ZIP.

18. Tous les chemins CSS, JS et images doivent être relatifs.

19. Retourner UNIQUEMENT le JSON correspondant au schema demandé.
"""

        prompt = f"""
Voici le DesignJSON complet du site :

---------------- DESIGN JSON ----------------

{design_json}

---------------- FIN DESIGN JSON ----------------

Génère maintenant le site complet.

Le résultat doit contenir :

- index.html
- toutes les autres pages HTML
- style.css
- script.js si nécessaire

Retourne uniquement un objet GeneratedSite valide.
"""

        response = self.client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=GeneratedSite,
                temperature=0.2,
            ),
        )

        return GeneratedSite.model_validate_json(response.text)