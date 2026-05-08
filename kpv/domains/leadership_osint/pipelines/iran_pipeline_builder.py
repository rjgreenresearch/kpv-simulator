from __future__ import annotations

from typing import Optional, Dict, Any

from .base_country_pipeline_builder import BaseCountryPipelineBuilder

from ..scrapers.iran_scraper import IranScraper
from ..parsers.iran_classical_parser import IranClassicalParser
from ..llm.iran_extractor import IranLLMExtractor
from ..ingestors.iran_ingestor import IranIngestor


class IranPipelineBuilder(BaseCountryPipelineBuilder):
    """
    DRY pipeline builder for the Iran OSINT ingestion system.

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
        return "IR"

    # ------------------------------------------------------------------
    # Component factories
    # ------------------------------------------------------------------
    def build_scraper(self):
        return IranScraper(
            data_root=self.data_root,
            enable_cache=self.enable_cache,
            proxies=self.proxies,
        )

    def build_classical_parser(self):
        return IranClassicalParser(data_root=self.data_root)

    def build_llm_extractor(self):
        return IranLLMExtractor(
            model_name=self.model_name,
            data_root=self.data_root,
        )

    def build_ingestor(self):
        return IranIngestor(data_root=self.data_root)
