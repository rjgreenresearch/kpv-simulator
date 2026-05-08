from __future__ import annotations

from typing import Optional, Dict, Any

from .base_country_pipeline_builder import BaseCountryPipelineBuilder

from ..scrapers.russia_scraper import RussiaScraper
from ..parsers.russia_classical_parser import RussiaClassicalParser
from ..llm.russia_extractor import RussiaLLMExtractor
from ..ingestors.russia_ingestor import RussiaIngestor


class RussiaPipelineBuilder(BaseCountryPipelineBuilder):
    """
    DRY pipeline builder for the Russian OSINT ingestion system.

    Inherits:
      - build_pipeline() from BaseCountryPipelineBuilder
      - logging, storage, configuration, wiring logic

    Defines only:
      - country_code
      - build_scraper()
      - build_classical_parser()
      - build_llm_extractor()
      - build_ingestor()
    """

    @property
    def country_code(self) -> str:
        return "RU"

    # ------------------------------------------------------------------
    # Component factories
    # ------------------------------------------------------------------
    def build_scraper(self):
        return RussiaScraper(
            data_root=self.data_root,
            enable_cache=self.enable_cache,
            proxies=self.proxies,
        )

    def build_classical_parser(self):
        return RussiaClassicalParser(data_root=self.data_root)

    def build_llm_extractor(self):
        return RussiaLLMExtractor(
            model_name=self.model_name,
            data_root=self.data_root,
        )

    def build_ingestor(self):
        return RussiaIngestor(data_root=self.data_root)
