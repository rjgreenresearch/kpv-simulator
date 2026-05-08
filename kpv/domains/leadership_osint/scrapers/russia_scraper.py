from __future__ import annotations

from typing import List, Dict, Any

from .base_scraper import BaseScraper
from ..utils.logger import get_logger


class RussiaScraper(BaseScraper):
    """
    Russia-specific scraper.

    Covers ALL TIERS:
      - Tier 1: Kremlin, Government, Duma, Federation Council
      - Tier 2: MOD, FSB, SVR, GRU, Rosgvardia
      - Tier 3: State media (TASS, RIA, Interfax, RG)
      - Tier 4: SOEs (Gazprom, Rosneft, Rostec) — optional but included

    Responsibilities:
      - define target URLs
      - apply Russia-specific request parameters
      - fix Cyrillic encoding issues
      - strip anti-bot JS and noise
    """

    def __init__(
        self,
        data_root: str = "./kpv_data",
        enable_cache: bool = True,
        proxies: Dict[str, str] = None,
    ):
        super().__init__(
            country_code="RU",
            data_root=data_root,
            enable_cache=enable_cache,
            proxies=proxies,
        )
        self.logger = get_logger("KPV.Scraper.RU", data_root)
        self.logger.info("Initialized RussiaScraper")

    # ------------------------------------------------------------------
    # Target URLs (ALL TIERS)
    # ------------------------------------------------------------------
    def get_target_urls(self) -> List[str]:
        """
        Comprehensive Russian leadership + narrative surface.
        """
        return [
            # Tier 1 — Government primary sources
            "http://kremlin.ru/",
            "http://government.ru/",
            "http://duma.gov.ru/",
            "http://council.gov.ru/",

            # Tier 2 — MOD + security services
            "http://mil.ru/",
            "http://fsb.ru/",
            "http://svr.gov.ru/",
            "http://rosgvard.ru/",

            # Tier 3 — State media (narrative + events)
            "https://tass.ru/politika",
            "https://ria.ru/politics/",
            "https://www.interfax.ru/",
            "https://rg.ru/",

            # Tier 4 — SOEs (leadership + board changes)
            "https://www.gazprom.ru/",
            "https://www.rosneft.com/",
            "https://rostec.ru/",
        ]

    # ------------------------------------------------------------------
    # Russia-specific request adjustments
    # ------------------------------------------------------------------
    def adjust_request_params(self, url: str) -> Dict[str, Any]:
        """
        Some Russian sites require:
          - persistent cookies (Kremlin/Government)
          - Cyrillic encoding hints
          - Accept-Language adjustments
        """
        params: Dict[str, Any] = {}

        # Kremlin/Government sometimes require session cookies
        if "kremlin.ru" in url or "government.ru" in url:
            params["cookies"] = {
                "sessionid": "placeholder-session",  # real session auto-managed
            }

        # Cyrillic encoding hints
        params.setdefault("headers", {})
        params["headers"]["Accept-Charset"] = "utf-8,windows-1251;q=0.7,*;q=0.7"
        params["headers"]["Accept-Language"] = "ru-RU,ru;q=0.9,en-US;q=0.8"

        return params

    # ------------------------------------------------------------------
    # HTML postprocessing
    # ------------------------------------------------------------------
    def postprocess_html(self, html: str, url: str) -> str:
        """
        Fix Cyrillic encoding issues and strip anti-scraping noise.
        """
        # Fix common mislabeling: windows-1251 served as ISO-8859-1
        try:
            if "charset=windows-1251" in html.lower() or "windows-1251" in html.lower():
                html = html.encode("ISO-8859-1").decode("windows-1251", errors="ignore")
        except Exception as e:
            self.logger.warning(f"Encoding normalization failed for {url}: {e}")

        # Remove anti-bot JS blocks
        for marker in ["<script>", "anti-bot", "captcha", "cloudflare"]:
            if marker in html:
                html = html.replace(marker, "")

        return html
