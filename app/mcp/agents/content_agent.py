class ContentAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, structure):

        prompt = f"""
Rédige un cahier des charges complet basé sur cette structure :

{structure}

Inclure :
- H1 / H2
- contenu SEO
- sections pages
- recommandations design
"""

        return self.llm.generate(prompt)