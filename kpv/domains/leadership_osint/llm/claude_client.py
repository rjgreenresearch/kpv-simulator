import os
import time
import json
import hashlib
from typing import Optional, Dict, Any

import requests

from ..utils.logger import get_logger


class ClaudeClient:
    """
    Thin, production-ready wrapper around the Claude API.

    Features:
      - API key loading from environment
      - retry logic with exponential backoff
      - structured logging
      - graceful error handling
      - optional response caching
      - strict JSON return behavior
    """

    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2

    def __init__(
        self,
        model: str = "claude-3-opus",
        data_root: str = "./kpv_data",
        enable_cache: bool = True,
    ):
        self.model = model
        self.data_root = data_root
        self.enable_cache = enable_cache

        self.logger = get_logger("KPV.LLM.ClaudeClient", data_root)

        self.api_key = os.environ.get("CLAUDE_API_KEY")
        if not self.api_key:
            self.logger.error("Claude API key not found in environment variable CLAUDE_API_KEY")
            raise RuntimeError("Missing Claude API key")

        self.base_url = "https://api.anthropic.com/v1/messages"

        if enable_cache:
            self.cache_dir = os.path.join(data_root, "llm_cache")
            os.makedirs(self.cache_dir, exist_ok=True)

        self.logger.info(f"ClaudeClient initialized with model={self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(self, prompt: str) -> str:
        """
        Generate a response from Claude.
        Returns raw text (expected to be JSON).
        """
        cache_key = self._cache_key(prompt)

        # --------------------------------------------------------------
        # Cache hit
        # --------------------------------------------------------------
        if self.enable_cache:
            cached = self._load_cache(cache_key)
            if cached is not None:
                self.logger.info(f"Cache hit for prompt_hash={cache_key}")
                return cached

        # --------------------------------------------------------------
        # API call with retries
        # --------------------------------------------------------------
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = self._call_api(prompt)
                text = self._extract_text(response)

                if self.enable_cache:
                    self._save_cache(cache_key, text)

                return text

            except Exception as e:
                self.logger.error(
                    f"Claude API call failed (attempt {attempt}/{self.MAX_RETRIES}): {e}"
                )

                if attempt == self.MAX_RETRIES:
                    raise

                sleep_time = self.BACKOFF_FACTOR ** attempt
                self.logger.info(f"Retrying in {sleep_time} seconds")
                time.sleep(sleep_time)

        # Should never reach here
        raise RuntimeError("Claude API call failed after all retries")

    # ------------------------------------------------------------------
    # Internal API call
    # ------------------------------------------------------------------
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        self.logger.info("Sending request to Claude API")

        response = requests.post(
            self.base_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=self.DEFAULT_TIMEOUT,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Claude API returned status {response.status_code}: {response.text}"
            )

        return response.json()

    # ------------------------------------------------------------------
    # Extract text from Claude response
    # ------------------------------------------------------------------
    def _extract_text(self, response: Dict[str, Any]) -> str:
        """
        Extract the assistant's text content from Claude's response.
        """
        try:
            content = response["content"]
            if not content:
                raise ValueError("Empty content array")

            # Claude returns: [{ "type": "text", "text": "..." }]
            first = content[0]
            if first.get("type") != "text":
                raise ValueError(f"Unexpected content type: {first}")

            return first["text"]

        except Exception as e:
            self.logger.error(f"Failed to extract text from Claude response: {e}")
            raise

    # ------------------------------------------------------------------
    # Caching
    # ------------------------------------------------------------------
    def _cache_key(self, prompt: str) -> str:
        h = hashlib.sha256()
        h.update(prompt.encode("utf-8"))
        return h.hexdigest()[:32]

    def _cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def _load_cache(self, key: str) -> Optional[str]:
        path = self._cache_path(key)
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to load cache file {path}: {e}")
            return None

    def _save_cache(self, key: str, text: str):
        path = self._cache_path(key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            self.logger.warning(f"Failed to save cache file {path}: {e}")
