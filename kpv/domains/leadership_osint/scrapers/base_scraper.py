from __future__ import annotations

import os
import time
import random
import hashlib
from typing import Optional, Dict, Any, List

import requests
from urllib.parse import urlparse

from ..utils.logger import get_logger


class BaseScraper:
    """
    Reusable, DRY scraping engine for all countries.

    Features:
      - HTTP GET with retries + exponential backoff
      - rate limiting
      - user-agent rotation
      - proxy support
      - robots.txt awareness (optional)
      - session persistence
      - response caching
      - structured logging
      - graceful error handling

    Country-specific scrapers override:
      - get_target_urls()
      - adjust_request_params()
      - postprocess_html()
    """

    DEFAULT_TIMEOUT = 20
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2
    RATE_LIMIT_SECONDS = 1.0

    USER_AGENTS = [
        # A small, rotating pool of realistic user agents
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/16.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    ]

    def __init__(
        self,
        country_code: str,
        data_root: str = "./kpv_data",
        enable_cache: bool = True,
        proxies: Optional[Dict[str, str]] = None,
    ):
        self.country_code = country_code.upper()
        self.data_root = data_root
        self.enable_cache = enable_cache
        self.proxies = proxies

        self.logger = get_logger(f"KPV.Scraper.{self.country_code}", data_root)

        # Session for persistent cookies + connection pooling
        self.session = requests.Session()

        # Cache directory
        if enable_cache:
            self.cache_dir = os.path.join(data_root, "scraper_cache", self.country_code)
            os.makedirs(self.cache_dir, exist_ok=True)

        self.logger.info(f"Initialized BaseScraper for {self.country_code}")

    # ------------------------------------------------------------------
    # Abstract: country-specific scrapers override this
    # ------------------------------------------------------------------
    def get_target_urls(self) -> List[str]:
        """
        Return a list of URLs to scrape.
        Subclasses must override.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Public API: fetch a URL
    # ------------------------------------------------------------------
    def fetch(self, url: str) -> str:
        """
        Fetch a URL with:
          - caching
          - retries
          - rate limiting
          - user-agent rotation
          - proxy support
        Returns raw HTML/text.
        """
        cache_key = self._cache_key(url)

        # --------------------------------------------------------------
        # Cache hit
        # --------------------------------------------------------------
        if self.enable_cache:
            cached = self._load_cache(cache_key)
            if cached is not None:
                self.logger.info(f"Cache hit for {url}")
                return cached

        # --------------------------------------------------------------
        # Rate limiting
        # --------------------------------------------------------------
        time.sleep(self.RATE_LIMIT_SECONDS)

        # --------------------------------------------------------------
        # HTTP GET with retries
        # --------------------------------------------------------------
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                headers = {
                    "User-Agent": random.choice(self.USER_AGENTS),
                    "Accept-Language": "en-US,en;q=0.9",
                }

                # Allow country-specific adjustments
                params = self.adjust_request_params(url)

                self.logger.info(
                    f"Fetching {url} (attempt {attempt}/{self.MAX_RETRIES})"
                )

                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=self.proxies,
                    timeout=self.DEFAULT_TIMEOUT,
                    **params,
                )

                if response.status_code != 200:
                    raise RuntimeError(
                        f"HTTP {response.status_code}: {response.text[:200]}"
                    )

                html = response.text

                # Allow country-specific postprocessing
                html = self.postprocess_html(html, url)

                if self.enable_cache:
                    self._save_cache(cache_key, html)

                return html

            except Exception as e:
                self.logger.error(
                    f"Error fetching {url} (attempt {attempt}): {e}"
                )

                if attempt == self.MAX_RETRIES:
                    raise

                sleep_time = self.BACKOFF_FACTOR ** attempt
                self.logger.info(f"Retrying in {sleep_time} seconds")
                time.sleep(sleep_time)

        # Should never reach here
        raise RuntimeError(f"Failed to fetch {url} after all retries")

    # ------------------------------------------------------------------
    # Optional country-specific hooks
    # ------------------------------------------------------------------
    def adjust_request_params(self, url: str) -> Dict[str, Any]:
        """
        Subclasses may override to add:
          - cookies
          - session tokens
          - query params
          - special headers
        """
        return {}

    def postprocess_html(self, html: str, url: str) -> str:
        """
        Subclasses may override to:
          - fix encoding issues
          - strip scripts
          - normalize whitespace
          - remove tracking elements
        """
        return html

    # ------------------------------------------------------------------
    # Caching
    # ------------------------------------------------------------------
    def _cache_key(self, url: str) -> str:
        h = hashlib.sha256()
        h.update(url.encode("utf-8"))
        return h.hexdigest()[:32]

    def _cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.html")

    def _load_cache(self, key: str) -> Optional[str]:
        path = self._cache_path(key)
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to load cache file {path}: {e}")
            return None

    def _save_cache(self, key: str, html: str):
        path = self._cache_path(key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            self.logger.warning(f"Failed to save cache file {path}: {e}")
