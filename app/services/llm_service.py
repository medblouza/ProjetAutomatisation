"""
LLMTool — thin wrapper around the Gemini API used by every agent.

Gemini 3.5 Flash-Lite:
- Low latency
- High throughput
- Large context window
- Structured JSON output support

The public interface remains unchanged so existing agents do not need
to be modified.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from google import genai
from google.genai import types

from app.utils.json_utils import LLMJsonError, safe_json_parse


DEFAULT_MODEL = "gemini-3.5-flash-lite"

MAX_TOKENS = 4096


class LLMGenerationError(Exception):
    """Raised when the LLM fails to produce a usable response after retries."""


class LLMTool:

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
    ):
        self.model = model

        self.client = genai.Client(
            api_key=api_key or os.environ.get("GEMINI_API_KEY")
        )

    def _call(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
    ) -> str:

        # Gemini 3.5 Flash-Lite does not require/use temperature.
        config_kwargs = {
            "max_output_tokens": MAX_TOKENS,
            "thinking_config": types.ThinkingConfig(
                thinking_level="minimal"
            ),
        }

        if system:
            config_kwargs["system_instruction"] = system

        config = types.GenerateContentConfig(**config_kwargs)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        return (response.text or "").strip()

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        expect_json: bool = False,
        temperature: float = 0.4,
        retry_prompt: Optional[str] = None,
        expected_root: str = "object",
    ) -> Any:
        """
        Generate content using Gemini.

        If expect_json=True:
            The response is parsed using safe_json_parse.

        On empty/invalid JSON:
            Retry once using retry_prompt if provided,
            otherwise retry the same prompt.

        expected_root:
            - "object" : JSON object {}
            - "array"  : JSON array []
            - "any"    : either

        Returns:
            Parsed JSON object when expect_json=True,
            otherwise raw string.
        """

        # ---------------------------------------------------------
        # FIRST ATTEMPT
        # ---------------------------------------------------------
        try:
            raw = self._call(
                prompt,
                system,
                temperature,
            )

        except Exception as e:
            raise LLMGenerationError(
                f"Gemini API error: {e}"
            ) from e

        print("\n========== LLM RAW RESPONSE ==========")
        print(raw)
        print("========== END LLM RAW RESPONSE ==========\n")

        # ---------------------------------------------------------
        # RAW TEXT RESPONSE
        # ---------------------------------------------------------
        if not expect_json:

            if not raw:
                raise LLMGenerationError(
                    "LLM returned an empty response"
                )

            return raw

        # ---------------------------------------------------------
        # JSON PARSING
        # ---------------------------------------------------------
        try:
            return safe_json_parse(
                raw,
                expected_root=expected_root
            )

        except LLMJsonError:
            pass

        # ---------------------------------------------------------
        # RETRY
        # ---------------------------------------------------------
        fallback_prompt = retry_prompt or prompt

        try:
            raw_retry = self._call(
                fallback_prompt,
                system,
                temperature=0.0,
            )

        except Exception as e:
            raise LLMGenerationError(
                f"Gemini API error during JSON retry: {e}"
            ) from e

        print("\n========== LLM RAW RESPONSE (RETRY) ==========")
        print(raw_retry)
        print("========== END LLM RAW RESPONSE (RETRY) ==========\n")

        # ---------------------------------------------------------
        # SECOND JSON PARSE
        # ---------------------------------------------------------
        try:
            return safe_json_parse(
                raw_retry,
                expected_root=expected_root
            )

        except LLMJsonError as e:
            raise LLMGenerationError(
                f"LLM failed to return valid JSON after retry: {e}"
            ) from e