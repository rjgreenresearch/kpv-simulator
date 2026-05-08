from __future__ import annotations

from typing import List, Dict, Any

from .base_scraper import BaseScraper
from ..utils.logger import get_logger


class IranScraper(BaseScraper):
    """
    Iran-specific scraper.

    Covers ALL TIERS:
      - Tier 1: Supreme Leader’s Office, Presidency, Majlis, Judiciary
      - Tier 2: IRGC, Artesh, LEF, MOIS
      - Tier 3: State media (IRNA, Tasnim, Fars)
      - Tier 4: Bonyads + SOEs (NIOC, NDFI, MAPNA)

    Responsibilities:
      - define target URLs
      - apply Iran-specific request parameters
      - normalize UTF-8 Persian text
      - strip anti-bot JS and noise
    """

    def __init__(
        self,
        data_root: str = "./kpv_data",
        enable_cache: bool = True,
        proxies: Dict[str, str] = None,
    ):
        super().__init__(
            country_code="IR",
            data_root=data_root,
            enable_cache=enable_cache,
            proxies=proxies,
        )
        self.logger = get_logger("KPV.Scraper.IR", data_root)
        self.logger.info("Initialized IranScraper")

    # ------------------------------------------------------------------
    # Target URLs (ALL TIERS)
    # ------------------------------------------------------------------
    def get_target_urls(self) -> List[str]:
        """
        Comprehensive Iranian leadership + narrative surface.
        """
        return [
            # Tier 1 — Government primary sources
            "https://leader.ir/",
            "https://president.ir/",
            "https://dolat.ir/",
            "https://parliran.ir/",
            "https:// judiciary.ir/",

            # Tier 2 — IRGC, Artesh, LEF, MOIS
            "https://www.sepahnews.com/",
            "https://aja.ir/",
            "https://www.police.ir/",
            "https://www.vaja.ir/",

            # Tier 3 — State media
            "https://www.irna.ir/",
            "https://www.tasnimnews.com/",
            "https://www.farsnews.ir/",

            # Tier 4 — Bonyads + SOEs
            "https://www.nioc.ir/",
            "https://www.ndfi.ir/",
            "https://www.mapnagroup.com/",
        ]

    # ------------------------------------------------------------------
    # Iran-specific request adjustments
    # ------------------------------------------------------------------
    def adjust_request_params(self, url: str) -> Dict[str, Any]:
        """
        Some Iranian sites require:
          - Accept-Language hints
          - UTF-8 enforcement
          - proxy routing
        """
        params: Dict[str, Any] = {}

        params.setdefault("headers", {})
        params["headers"]["Accept-Language"] = "fa-IR,fa;q=0.9,en-US;q=0.8"
        params["headers"]["Accept-Charset"] = "utf-8,*;q=0.7"

        return params

    # ------------------------------------------------------------------
    # HTML postprocessing
    # ------------------------------------------------------------------
    def postprocess_html(self, html: str, url: str) -> str:
        """
        Normalize UTF-8 Persian text and strip anti-scraping noise.
        """
        # Normalize Persian UTF-8
        try:
            html = html.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
        except Exception as e:
            self.logger.warning(f"UTF-8 normalization failed for {url}: {e}")

        # Remove anti-bot JS blocks
        for marker in ["<script>", "captcha", "cloudflare", "anti-bot"]:
            if marker in html:
                html = html.replace(marker, "")

        return html
