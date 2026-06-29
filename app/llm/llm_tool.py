"""
app/tools/llm_tool.py
Interface avec Groq API (llama3.2) — rapide, robuste, sans Ollama.
pip install groq
"""
import os
import json
import logging
import re
from groq import Groq

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"
MAX_RETRIES  = 2
MAX_TOKENS   = 4096


class LLMTool:
    def __init__(
        self,
        api_key: str = "",
        model: str = GROQ_MODEL,
    ):
        self.model  = model
        self.client = Groq(api_key=api_key or GROQ_API_KEY)

    def generate(self, prompt: str, expect_json: bool = False) -> str:
        """
        Envoie un prompt à Groq et retourne le texte généré.
        Ne lève jamais d'exception — retourne "" en cas d'échec total.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"[LLM] Attempt {attempt} — model: {self.model}")

                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=MAX_TOKENS,
                    temperature=0.3,
                )

                output = completion.choices[0].message.content or ""
                output = output.strip()

                if not output:
                    logger.warning(f"[LLM] Réponse vide (attempt {attempt})")
                    continue

                if expect_json:
                    output = self._clean_json_response(output)

                logger.debug(f"[LLM] ✅ Succès — {len(output)} caractères")
                return output

            except Exception as e:
                logger.error(f"[LLM] Erreur attempt {attempt} : {e}")
                if attempt == MAX_RETRIES:
                    return ""

        return ""

    @staticmethod
    def _clean_json_response(text: str) -> str:
        """Nettoie la réponse LLM pour extraire du JSON valide."""
        # Supprimer les blocs markdown
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()

        # Valider directement
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass

        # Extraire le premier objet JSON {}
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            candidate = match.group()
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        # Extraire le premier tableau JSON []
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            candidate = match.group()
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        return text