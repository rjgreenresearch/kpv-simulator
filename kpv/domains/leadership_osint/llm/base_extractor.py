from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import json

from ..utils.logger import get_logger


@dataclass
class LLMExtractionResult:
    """
    Container for LLM extraction results.
    Keeps raw text, parsed payload, and any warnings/errors.
    """
    success: bool
    data: Dict[str, Any]
    warnings: List[str]
    error: Optional[str] = None
    model: Optional[str] = None
    prompt_hash: Optional[str] = None


class BaseLLMExtractor(ABC):
    """
    Base class for all LLM-backed extractors.

    Responsibilities:
      - Build prompts
      - Call an underlying LLM client (Claude, etc.)
      - Enforce structured JSON output
      - Validate minimal schema
      - Log all key events
      - Fail gracefully with empty-but-valid structures
    """

    def __init__(
        self,
        country_code: str,
        model_name: str,
        client: Any,
        data_root: str = "./kpv_data",
    ):
        """
        :param country_code: ISO-like country code (CN, RU, IR, KP, etc.)
        :param model_name:   Underlying LLM model identifier (e.g., 'claude-3-opus')
        :param client:       An object exposing `generate(prompt: str) -> str`
        :param data_root:    Root path for logging and optional caching
        """
        self.country_code = country_code.upper()
        self.model_name = model_name
        self.client = client
        self.data_root = data_root

        self.logger = get_logger(f"KPV.LLM.{self.country_code}", data_root)
        self.logger.info(
            f"Initialized BaseLLMExtractor for {self.country_code} using model {self.model_name}"
        )

    # ------------------------------------------------------------------
    # Public high-level API
    # ------------------------------------------------------------------
    def extract_entities(self, text: str) -> LLMExtractionResult:
        """
        High-level entrypoint for entity extraction.
        Returns a structured LLMExtractionResult with graceful failure behavior.
        """
        return self._run_extraction(
            text=text,
            task="entities",
            expected_root_keys=["persons", "organizations"],
        )

    def extract_relationships(self, text: str) -> LLMExtractionResult:
        """
        High-level entrypoint for relationship extraction.
        """
        return self._run_extraction(
            text=text,
            task="relationships",
            expected_root_keys=["edges"],
        )

    def extract_events(self, text: str) -> LLMExtractionResult:
        """
        High-level entrypoint for event extraction (promotions, purges, reshuffles, etc.).
        """
        return self._run_extraction(
            text=text,
            task="events",
            expected_root_keys=["events"],
        )

    # ------------------------------------------------------------------
    # Core execution pipeline
    # ------------------------------------------------------------------
    def _run_extraction(
        self,
        text: str,
        task: str,
        expected_root_keys: List[str],
    ) -> LLMExtractionResult:
        """
        Shared execution path for all extraction tasks.
        Handles:
          - prompt construction
          - LLM invocation
          - JSON parsing
          - minimal validation
          - logging
          - graceful fallback
        """
        if not text or not text.strip():
            self.logger.warning(f"LLM extraction requested with empty text for task={task}")
            return self._empty_result(expected_root_keys, warning="Empty input text")

        try:
            prompt = self.build_prompt(text=text, task=task)
        except Exception as e:
            msg = f"Failed to build prompt for task={task}: {e}"
            self.logger.error(msg)
            return self._empty_result(expected_root_keys, error=msg)

        prompt_hash = self._hash_prompt(prompt)

        self.logger.info(
            f"Invoking LLM for task={task}, country={self.country_code}, "
            f"model={self.model_name}, prompt_hash={prompt_hash}"
        )

        try:
            raw_response = self.client.generate(prompt)
        except Exception as e:
            msg = f"LLM client error for task={task}: {e}"
            self.logger.error(msg)
            return self._empty_result(expected_root_keys, error=msg, prompt_hash=prompt_hash)

        try:
            parsed = self._parse_json_response(raw_response)
        except Exception as e:
            msg = f"Failed to parse LLM JSON response for task={task}: {e}"
            self.logger.error(msg)
            return self._empty_result(
                expected_root_keys,
                error=msg,
                prompt_hash=prompt_hash,
            )

        warnings = self._validate_minimal_structure(parsed, expected_root_keys)

        self.logger.info(
            f"LLM extraction completed for task={task}, "
            f"warnings={len(warnings)}, prompt_hash={prompt_hash}"
        )

        return LLMExtractionResult(
            success=True,
            data=parsed,
            warnings=warnings,
            error=None,
            model=self.model_name,
            prompt_hash=prompt_hash,
        )

    # ------------------------------------------------------------------
    # Abstract prompt builder
    # ------------------------------------------------------------------
    @abstractmethod
    def build_prompt(self, text: str, task: str) -> str:
        """
        Subclasses must implement a country- and task-specific prompt builder.

        The prompt MUST instruct the model to:
          - return STRICT JSON
          - use a known root structure (e.g., { "persons": [], "organizations": [] })
          - avoid commentary outside JSON
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # JSON parsing and minimal validation
    # ------------------------------------------------------------------
    def _parse_json_response(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse the raw LLM response as JSON.
        If the model occasionally wraps JSON in text, subclasses can override
        this method to implement more robust extraction.
        """
        raw_response = raw_response.strip()
        return json.loads(raw_response)

    def _validate_minimal_structure(
        self,
        payload: Dict[str, Any],
        expected_root_keys: List[str],
    ) -> List[str]:
        """
        Perform minimal structural validation:
          - ensure expected root keys exist
          - ensure they are of the correct type (usually list)
        Returns a list of warnings (non-fatal).
        """
        warnings: List[str] = []

        for key in expected_root_keys:
            if key not in payload:
                warnings.append(f"Missing expected root key: '{key}'")
                payload[key] = []
                continue

            if not isinstance(payload[key], list):
                warnings.append(f"Root key '{key}' is not a list; coercing to empty list")
                payload[key] = []

        return warnings

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _empty_result(
        self,
        expected_root_keys: List[str],
        warning: Optional[str] = None,
        error: Optional[str] = None,
        prompt_hash: Optional[str] = None,
    ) -> LLMExtractionResult:
        """
        Construct a safe, empty result object with the expected structure.
        """
        data: Dict[str, Any] = {key: [] for key in expected_root_keys}
        warnings: List[str] = []
        if warning:
            warnings.append(warning)

        return LLMExtractionResult(
            success=False,
            data=data,
            warnings=warnings,
            error=error,
            model=self.model_name,
            prompt_hash=prompt_hash,
        )

    def _hash_prompt(self, prompt: str) -> str:
        """
        Lightweight, deterministic hash for logging/caching.
        Avoids pulling in heavy dependencies; not for security use.
        """
        import hashlib

        h = hashlib.sha256()
        h.update(prompt.encode("utf-8"))
        return h.hexdigest()[:16]
