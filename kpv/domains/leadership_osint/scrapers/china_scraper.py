from __future__ import annotations

from typing import List, Dict, Any

from .base_scraper import BaseScraper
from ..utils.logger import get_logger


class ChinaScraper(BaseScraper):
    """
    China-specific scraper.

    Responsibilities:
      - define starting URLs for PRC/CCP/PLA/SOE leadership sources
      - apply China-specific request parameters (proxies, headers, cookies)
      - fix common encoding issues (GB2312/GBK → UTF-8)
      - strip anti-scraping noise where possible

    All heavy lifting (retries, caching, rate limiting, etc.)
    is inherited from BaseScraper.
    """

    def __init__(
        self,
        data_root: str = "./kpv_data",
        enable_cache: bool = True,
        proxies: Dict[str, str] = None,
    ):
        super().__init__(
            country_code="CN",
            data_root=data_root,
            enable_cache=enable_cache,
            proxies=proxies,
        )
        self.logger = get_logger("KPV.Scraper.CN", data_root)
        self.logger.info("Initialized ChinaScraper")

    # ------------------------------------------------------------------
    # Starting URLs
    # ------------------------------------------------------------------
    def get_target_urls(self) -> List[str]:
        """
        Core PRC leadership sources:
          - State Council
          - Ministry of National Defense
          - CCP leadership directories
          - PLA Daily leadership pages
          - Xinhua political section
        """
        return [
            "http://www.gov.cn/guowuyuan/",
            "http://www.mod.gov.cn/",
            "http://www.xinhuanet.com/politics/",
            "http://www.81.cn/",
        ]

    # ------------------------------------------------------------------
    # China-specific request adjustments
    # ------------------------------------------------------------------
    def adjust_request_params(self, url: str) -> Dict[str, Any]:
        """
        Some PRC sites require:
          - GBK/GB2312 encoding
          - persistent cookies
          - special headers to avoid 403
        """
        params: Dict[str, Any] = {}

        # Add cookies for gov.cn if needed
        if "gov.cn" in url:
            params["cookies"] = {
                "wzws_sessionid": "fake-session-id",  # placeholder; real session set automatically
            }

        # Some sites require explicit encoding override
        if "81.cn" in url:
            params["headers"] = {
                "Accept-Charset": "GB2312,utf-8;q=0.7,*;q=0.7",
            }

        return params

    # ------------------------------------------------------------------
    # HTML postprocessing
    # ------------------------------------------------------------------
    def postprocess_html(self, html: str, url: str) -> str:
        """
        Fix common PRC encoding issues and strip anti-scraping noise.
        """
        # Normalize encoding if site incorrectly labels GBK as ISO-8859-1
        try:
            if "charset=gb" in html.lower() or "gb2312" in html.lower():
                html = html.encode("ISO-8859-1").decode("gbk", errors="ignore")
        except Exception as e:
            self.logger.warning(f"Encoding normalization failed for {url}: {e}")

        # Remove common anti-scraping JS blocks
        for marker in ["<script>", "wzws", "anti-crawler"]:
            if marker in html:
                html = html.replace(marker, "")

        return html
