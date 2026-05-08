from __future__ import annotations

from typing import Optional, Dict, Any

from .base_country_pipeline_builder import BaseCountryPipelineBuilder

from ..scrapers.north_korea_scraper import NorthKoreaScraper
from ..parsers.north_korea_classical_parser import NorthKoreaClassicalParser
from ..llm.north_korea_extractor import NorthKoreaLLMExtractor
from ..ingestors.north_korea_ingestor import NorthKoreaIngestor


class NorthKoreaPipelineBuilder(BaseCountryPipelineBuilder):
    """
    DRY pipeline builder for the DPRK OSINT ingestion system.

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
        return "KP"

    # ------------------------------------------------------------------
    # Component factories
    # ------------------------------------------------------------------
    def build_scraper(self):
        return NorthKoreaScraper(
            data_root=self.data_root,
            enable_cache=self.enable_cache,
            proxies=self.proxies,
        )

    def build_classical_parser(self):
        return NorthKoreaClassicalParser(data_root=self.data_root)

    def build_llm_extractor(self):
        return NorthKoreaLLMExtractor(
            model_name=self.model_name,
            data_root=self.data_root,
        )

    def build_ingestor(self):
        return NorthKoreaIngestor(data_root=self.data_root)
