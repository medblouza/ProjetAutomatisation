import requests

class LLMTool:
    def __init__(self, url="http://localhost:11434/api/generate", model="llama3.2"):
        self.url = url
        self.model = model

    def generate(self, prompt):
        response = requests.post(self.url, json={
            "model": self.model,
            "prompt": prompt,
            "stream": False
        })

        return response.json()["response"]