class AnalyzerAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, data):

        prompt = f"""
Analyse les données client suivantes et retourne un JSON STRICT :

{data}

Format attendu :
{{
  "activity": "",
  "target": "",
  "services": [],
  "strengths": []
}}
"""

        result = self.llm.generate(prompt)
        return eval(result)