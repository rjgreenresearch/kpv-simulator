from __future__ import annotations

from typing import Any

from .base_extractor import BaseLLMExtractor
from .china_profile import ChinaLLMProfile
from .claude_client import ClaudeClient

from ..utils.logger import get_logger


class ChinaLLMExtractor(BaseLLMExtractor):
    """
    China-specific LLM extractor.

    Combines:
      - BaseLLMExtractor (execution pipeline)
      - ClaudeClient (API access)
      - ChinaLLMProfile (linguistic + political patterns)
    """

    def __init__(
        self,
        model_name: str = "claude-3-opus",
        data_root: str = "./kpv_data",
        client: Any = None,
        profile: ChinaLLMProfile = None,
    ):
        self.profile = profile or ChinaLLMProfile()
        self.logger = get_logger("KPV.LLM.CN.Extractor", data_root)

        # If no client is provided, create a ClaudeClient
        if client is None:
            client = ClaudeClient(model=model_name, data_root=data_root)

        super().__init__(
            country_code="CN",
            model_name=model_name,
            client=client,
            data_root=data_root,
        )

        self.logger.info("ChinaLLMExtractor initialized")

    # ------------------------------------------------------------------
    # Prompt builder (country + task aware)
    # ------------------------------------------------------------------
    def build_prompt(self, text: str, task: str) -> str:
        """
        Build a prompt using the ChinaLLMProfile templates.
        Ensures STRICT JSON output and country-specific extraction rules.
        """
        if task == "entities":
            template = self.profile.entity_prompt_template
        elif task == "relationships":
            template = self.profile.relationship_prompt_template
        elif task == "events":
            template = self.profile.event_prompt_template
        else:
            raise ValueError(f"Unknown extraction task: {task}")

        prompt = self.profile.render_prompt(template, text)

        # Log prompt hash for reproducibility
        self.logger.info(
            f"Built prompt for task={task}, length={len(prompt)} chars"
        )

        return prompt