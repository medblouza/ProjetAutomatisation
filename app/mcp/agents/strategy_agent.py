class StrategyAgent:
    def __init__(self, llm):
        self.llm = llm

    def run(self, data):

        prompt = f"""
A partir de cette analyse, génère une stratégie digitale.

{data}

Format JSON :
{{
  "objectives": [],
  "messages": []
}}
"""
        result = self.llm.generate(prompt)
        return eval(result)