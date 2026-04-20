class QAAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, content):

        prompt = f"""
Corrige et améliore ce cahier des charges.

{content}

Retourne :
- version corrigée
- score qualité sur 100

Format :
{{
  "score": 0,
  "content": ""
}}
"""
        result = self.llm.generate(prompt)
        return eval(result)