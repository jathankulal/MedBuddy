"""Gemini integration client (backend only).

Reads GEMINI_API_KEY and GEMINI_MODEL from backend configuration. Never
exposes the API key to the frontend.
"""

from typing import Optional

from backend.config import settings


class GeminiClient:
    """Client for Google Gemini generation (backend-side only)."""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the GenAI client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is not configured")
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def is_configured(self) -> bool:
        """Return True if a Gemini API key is available."""
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Generate text using Gemini.

        Raises RuntimeError if the API call fails.
        """
        if not self.is_configured():
            raise RuntimeError("Gemini API key is not configured")

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            return response.text or ""
        except Exception as exc:
            raise RuntimeError(f"Gemini generation failed: {exc}") from exc
