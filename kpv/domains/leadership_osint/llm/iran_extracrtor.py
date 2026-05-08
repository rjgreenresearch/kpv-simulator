from __future__ import annotations

from typing import Any

from .base_extractor import BaseLLMExtractor
from .iran_profile import IranLLMProfile
from .claude_client import ClaudeClient

from ..utils.logger import get_logger


class IranLLMExtractor(BaseLLMExtractor):
    """
    Iran-specific LLM extractor.

    Combines:
      - BaseLLMExtractor (prompt → LLM → JSON → validation)
      - ClaudeClient (API access)
      - IranLLMProfile (naming, clerical hierarchy, IRGC ranks, ministries)
    """

    def __init__(
        self,
        model_name: str = "claude-3-opus",
        data_root: str = "./kpv_data",
        client: Any = None,
        profile: IranLLMProfile = None,
    ):
        self.profile = profile or IranLLMProfile()
        self.logger = get_logger("KPV.LLM.IR.Extractor", data_root)

        # Instantiate ClaudeClient if none provided
        if client is None:
            client = ClaudeClient(model=model_name, data_root=data_root)

        super().__init__(
            country_code="IR",
            model_name=model_name,
            client=client,
            data_root=data_root,
        )

        self.logger.info("IranLLMExtractor initialized")

    # ------------------------------------------------------------------
    # Prompt builder (country + task aware)
    # ------------------------------------------------------------------
    def build_prompt(self, text: str, task: str) -> str:
        """
        Build a prompt using the IranLLMProfile templates.
        Ensures STRICT JSON output and Iran-specific extraction rules.
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
            f"Built IR prompt for task={task}, length={len(prompt)} chars"
        )

        return prompt
