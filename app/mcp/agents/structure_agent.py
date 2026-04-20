'''
class StructureAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, data):

        prompt = f"""
Crée une arborescence de site web.

{data}

Format JSON :
{{
  "pages": [
    {{
      "name": "",
      "sections": []
    }}
  ]
}}
"""
        result = self.llm.generate(prompt)
        return eval(result)
'''
import json

class StructureAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, data):

        prompt = f"""
Crée une arborescence de site web.

{data}

Réponds STRICTEMENT en JSON valide.

Format :
{{
  "pages": [
    {{
      "name": "",
      "sections": []
    }}
  ]
}}
"""

        result = self.llm.generate(prompt)

        try:
            parsed = json.loads(result)
        except:
            print("Erreur JSON:", result)
            return {"pages": []}

        # 🔥 FIX CRUCIAL : forcer string
        for page in parsed.get("pages", []):
            page["name"] = str(page.get("name", ""))

            sections = page.get("sections", [])
            page["sections"] = [str(s) for s in sections if s is not None]

        return parsed