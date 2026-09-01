# app/tools/llm_tool.py
# Interface avec Gemini API (gemini-2.0-flash) — rapide, robuste.
# pip install google-generativeai

import os
import json
import logging
import re
import google.generativeai as genai

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Modèles disponibles : gemini-2.0-flash, gemini-2.0-pro, gemini-1.5-pro, gemini-1.5-flash
GEMINI_MODEL   = "gemini-3.5-flash-lite"
MAX_RETRIES    = 2
MAX_TOKENS     = 4096


class LLMTool:
    def __init__(
        self,
        api_key: str = "",
        model: str = GEMINI_MODEL,
    ):
        self.model = model
        genai.configure(api_key=api_key or GEMINI_API_KEY)
        self.client = genai.GenerativeModel(model)

    def generate(self, prompt: str, expect_json: bool = False) -> str:
        """
        Envoie un prompt à Gemini et retourne le texte généré.
        Ne lève jamais d'exception — retourne "" en cas d'échec total.
        """
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"[LLM] Attempt {attempt} — model: {self.model}")

                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        "max_output_tokens": MAX_TOKENS,
                        "temperature": 0.3,
                    }
                )

                output = response.text or ""
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