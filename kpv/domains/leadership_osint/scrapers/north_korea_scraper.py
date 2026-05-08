from __future__ import annotations

from typing import List, Dict, Any

from .base_scraper import BaseScraper
from ..utils.logger import get_logger


class NorthKoreaScraper(BaseScraper):
    """
    DPRK-specific scraper.

    Covers ALL TIERS:
      - Tier 1: WPK, State Affairs Commission, Cabinet
      - Tier 2: KPA (all services), State Security, internal security
      - Tier 3: State media (KCNA, Rodong Sinmun)
      - Tier 4: DPRK SOEs and economic ministries

    Responsibilities:
      - define target URLs
      - apply DPRK-specific request parameters
      - normalize UTF-8 Korean text
      - strip anti-bot JS and noise
    """

    def __init__(
        self,
        data_root: str = "./kpv_data",
        enable_cache: bool = True,
        proxies: Dict[str, str] = None,
    ):
        super().__init__(
            country_code="KP",
            data_root=data_root,
            enable_cache=enable_cache,
            proxies=proxies,
        )
        self.logger = get_logger("KPV.Scraper.KP", data_root)
        self.logger.info("Initialized NorthKoreaScraper")

    # ------------------------------------------------------------------
    # Target URLs (ALL TIERS)
    # ------------------------------------------------------------------
    def get_target_urls(self) -> List[str]:
        """
        Comprehensive DPRK leadership + narrative surface.
        """
        return [
            # Tier 1 — Party + State
            "http://www.kcna.kp/",                 # KCNA (primary)
            "http://www.rodong.rep.kp/",           # Rodong Sinmun
            "http://naenara.com.kp/",              # Government portal
            "http://www.korea-dpr.com/",           # Foreign-facing portal

            # Tier 2 — Military + Security
            "http://www.mod.gov.kp/",              # Ministry of Defence (if reachable)
            "http://www.kpa.gov.kp/",              # KPA (varies by mirror)
            "http://www.state-security.gov.kp/",   # State Security (rarely reachable)

            # Tier 3 — Additional state media mirrors
            "http://kcna.kp/",                     # Alternate KCNA mirror
            "http://www.kcna.co.jp/",              # Japanese mirror (stable)

            # Tier 4 — SOEs + economic ministries
            "http://www.ma.gov.kp/",               # Ministry of Agriculture
            "http://www.me.gov.kp/",               # Ministry of Electric Power
            "http://www.mof.gov.kp/",              # Ministry of Finance
        ]

    # ------------------------------------------------------------------
    # DPRK-specific request adjustments
    # ------------------------------------------------------------------
    def adjust_request_params(self, url: str) -> Dict[str, Any]:
        """
        DPRK sites often require:
          - Accept-Language hints
          - UTF-8 enforcement
          - proxy routing
        """
        params: Dict[str, Any] = {}

        params.setdefault("headers", {})
        params["headers"]["Accept-Language"] = "ko-KP,ko;q=0.9,en-US;q=0.8"
        params["headers"]["Accept-Charset"] = "utf-8,*;q=0.7"

        return params

    # ------------------------------------------------------------------
    # HTML postprocessing
    # ------------------------------------------------------------------
    def postprocess_html(self, html: str, url: str) -> str:
        """
        Normalize UTF-8 Korean text and strip anti-scraping noise.
        """
        # Normalize Korean UTF-8
        try:
            html = html.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
        except Exception as e:
            self.logger.warning(f"UTF-8 normalization failed for {url}: {e}")

        # Remove anti-bot JS blocks
        for marker in ["<script>", "captcha", "cloudflare", "anti-bot"]:
            if marker in html:
                html = html.replace(marker, "")

        return html
