from __future__ import annotations

from typing import Any

from .base_extractor import BaseLLMExtractor
from .north_korea_profile import NorthKoreaLLMProfile
from .claude_client import ClaudeClient

from ..utils.logger import get_logger


class NorthKoreaLLMExtractor(BaseLLMExtractor):
    """
    DPRK-specific LLM extractor.

    Combines:
      - BaseLLMExtractor (prompt → LLM → JSON → validation)
      - ClaudeClient (API access)
      - NorthKoreaLLMProfile (naming, WPK hierarchy, KPA ranks)
    """

    def __init__(
        self,
        model_name: str = "claude-3-opus",
        data_root: str = "./kpv_data",
        client: Any = None,
        profile: NorthKoreaLLMProfile = None,
    ):
        self.profile = profile or NorthKoreaLLMProfile()
        self.logger = get_logger("KPV.LLM.KP.Extractor", data_root)

        # Instantiate ClaudeClient if none provided
        if client is None:
            client = ClaudeClient(model=model_name, data_root=data_root)

        super().__init__(
            country_code="KP",
            model_name=model_name,
            client=client,
            data_root=data_root,
        )

        self.logger.info("NorthKoreaLLMExtractor initialized")

    # ------------------------------------------------------------------
    # Prompt builder (country + task aware)
    # ------------------------------------------------------------------
    def build_prompt(self, text: str, task: str) -> str:
        """
        Build a prompt using the NorthKoreaLLMProfile templates.
        Ensures STRICT JSON output and DPRK-specific extraction rules.
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

        self.logger.info(
            f"Built KP prompt for task={task}, length={len(prompt)} chars"
        )

        return prompt
