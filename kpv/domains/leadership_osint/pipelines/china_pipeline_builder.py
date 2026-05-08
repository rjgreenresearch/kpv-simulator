from __future__ import annotations

from typing import Optional, Dict, Any

from .base_country_pipeline_builder import BaseCountryPipelineBuilder

from ..scrapers.china_scraper import ChinaScraper
from ..parsers.china_classical_parser import ChinaClassicalParser
from ..llm.china_extractor import ChinaLLMExtractor
from ..ingestors.china_ingestor import ChinaIngestor


class ChinaPipelineBuilder(BaseCountryPipelineBuilder):
    """
    DRY pipeline builder for the China OSINT ingestion system.

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
        return "CN"

    # ------------------------------------------------------------------
    # Component factories
    # ------------------------------------------------------------------
    def build_scraper(self):
        return ChinaScraper(
            data_root=self.data_root,
            enable_cache=self.enable_cache,
            proxies=self.proxies,
        )

    def build_classical_parser(self):
        return ChinaClassicalParser(data_root=self.data_root)

    def build_llm_extractor(self):
        return ChinaLLMExtractor(
            model_name=self.model_name,
            data_root=self.data_root,
        )

    def build_ingestor(self):
        return ChinaIngestor(data_root=self.data_root)