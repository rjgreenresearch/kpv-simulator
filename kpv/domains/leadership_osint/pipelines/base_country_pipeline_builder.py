from __future__ import annotations

from typing import Optional, Dict, Any

from ..utils.logger import get_logger
from ..utils.storage import StorageManager
from .scraper_pipeline import ScraperPipeline


class BaseCountryPipelineBuilder:
    """
    DRY, reusable base class for constructing country-specific OSINT pipelines.

    Responsibilities:
      - define the assembly sequence for:
          * scraper
          * classical parser
          * LLM extractor
          * hybrid parser
          * ingestor
          * pipeline
      - enforce consistent wiring across all countries
      - centralize configuration (data_root, proxies, model_name, caching)
      - provide overridable factory methods for subclasses

    Subclasses must override:
      - build_scraper()
      - build_classical_parser()
      - build_llm_extractor()
      - build_ingestor()
      - country_code property
    """

    def __init__(
        self,
        data_root: str = "./kpv_data",
        enable_cache: bool = True,
        proxies: Optional[Dict[str, str]] = None,
        model_name: str = "claude-3-opus",
    ):
        self.data_root = data_root
        self.enable_cache = enable_cache
        self.proxies = proxies
        self.model_name = model_name

        self.storage = StorageManager(data_root)
        self.logger = get_logger("KPV.Builder.Base", data_root)

        self.logger.info(
            f"Initialized BaseCountryPipelineBuilder "
            f"(model={model_name}, cache={enable_cache})"
        )

    # ------------------------------------------------------------------
    # Abstract properties / methods
    # ------------------------------------------------------------------
    @property
    def country_code(self) -> str:
        raise NotImplementedError("Subclasses must define country_code")

    def build_scraper(self):
        raise NotImplementedError("Subclasses must implement build_scraper()")

    def build_classical_parser(self):
        raise NotImplementedError("Subclasses must implement build_classical_parser()")

    def build_llm_extractor(self):
        raise NotImplementedError("Subclasses must implement build_llm_extractor()")

    def build_ingestor(self):
        raise NotImplementedError("Subclasses must implement build_ingestor()")

    # ------------------------------------------------------------------
    # Optional override: hybrid parser
    # ------------------------------------------------------------------
    def build_hybrid_parser(self, classical_parser, llm_extractor):
        """
        Subclasses may override to customize hybrid parser behavior.
        Default implementation uses LLMEnhancedParser.
        """
        from ..parsers.llm_enhanced_parser import LLMEnhancedParser

        return LLMEnhancedParser(
            country_code=self.country_code,
            classical_parser=classical_parser,
            llm_extractor=llm_extractor,
            data_root=self.data_root,
        )

    # ------------------------------------------------------------------
    # Pipeline assembly
    # ------------------------------------------------------------------
    def build_pipeline(self) -> ScraperPipeline:
        """
        Construct and return a fully configured ScraperPipeline.
        This method is identical for all countries — DRY.
        """
        self.logger.info(f"Building pipeline for {self.country_code}")

        # 1. Scraper
        scraper = self.build_scraper()

        # 2. Classical parser
        classical_parser = self.build_classical_parser()

        # 3. LLM extractor
        llm_extractor = self.build_llm_extractor()

        # 4. Hybrid parser
        hybrid_parser = self.build_hybrid_parser(classical_parser, llm_extractor)

        # 5. Ingestor
        ingestor = self.build_ingestor()

        # 6. Pipeline
        pipeline = ScraperPipeline(
            country_code=self.country_code,
            scraper=scraper,
            parser=hybrid_parser,
            ingestor=ingestor,
            storage=self.storage,
            data_root=self.data_root,
        )

        self.logger.info(f"Pipeline successfully built for {self.country_code}")
        return pipeline
