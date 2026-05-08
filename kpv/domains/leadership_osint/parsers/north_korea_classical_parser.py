from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup

from ..utils.logger import get_logger


class NorthKoreaClassicalParser:
    """
    Deterministic HTML parser for DPRK leadership sources.

    Responsibilities:
      - Extract structured data from:
          * WPK hierarchy
          * State Affairs Commission
          * Cabinet (Naegak)
          * KPA (all services)
          * State Security & internal security
      - Identify Korean names (family name first)
      - Detect narrative text (KCNA, Rodong Sinmun)
      - Detect ambiguous fields to trigger LLM fallback
    """

    def __init__(self, data_root: str = "./kpv_data"):
        self.data_root = data_root
        self.logger = get_logger("KPV.Parser.KP.Classical", data_root)
        self.logger.info("Initialized NorthKoreaClassicalParser")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse(self, html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")

        persons = []
        orgs = []
        edges = []

        # 1. Leadership tables (WPK, SAC, Cabinet, KPA)
        table_results = self._parse_tables(soup)
        persons.extend(table_results["persons"])
        orgs.extend(table_results["organizations"])
        edges.extend(table_results["edges"])

        # 2. Leadership lists (common in KCNA/Rodong)
        list_results = self._parse_leadership_lists(soup)
        persons.extend(list_results["persons"])
        orgs.extend(list_results["organizations"])
        edges.extend(list_results["edges"])

        # 3. Narrative detection (KCNA, Rodong Sinmun)
        narrative_detected = self._detect_narrative_text(soup)

        # 4. Ambiguity detection
        ambiguous = self._detect_ambiguity(persons)

        return {
            "persons": persons,
            "organizations": orgs,
            "edges": edges,
            "events": [],
            "narrative_text_detected": narrative_detected,
            "ambiguous_fields": ambiguous,
        }

    # ------------------------------------------------------------------
    # Leadership tables (WPK, SAC, Cabinet, KPA)
    # ------------------------------------------------------------------
    def _parse_tables(self, soup: BeautifulSoup) -> Dict[str, Any]:
        persons = []
        orgs = []
        edges = []

        tables = soup.find_all("table")
        if not tables:
            return {"persons": [], "organizations": [], "edges": []}

        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                if len(cols) < 2:
                    continue

                name = cols[0]
                position = cols[1]

                if self._is_korean_name(name):
                    persons.append({
                        "name_native": name,
                        "name_latin": None,
                        "aliases": [],
                        "current_position": position,
                        "service_or_agency": None,
                        "rank_or_grade": None,
                        "thematic_keywords": [],
                    })

        return {"persons": persons, "organizations": orgs, "edges": edges}

    # ------------------------------------------------------------------
    # Leadership lists (KCNA, Rodong Sinmun)
    # ------------------------------------------------------------------
    def _parse_leadership_lists(self, soup: BeautifulSoup) -> Dict[str, Any]:
        persons = []
        orgs = []
        edges = []

        for li in soup.find_all("li"):
            text = li.get_text(strip=True)
            if not text:
                continue

            parts = (
                text.replace("—", "-")
                    .replace("–", "-")
                    .replace(":", "-")
                    .split("-")
            )

            if len(parts) < 2:
                continue

            name = parts[0].strip()
            position = parts[1].strip()

            if self._is_korean_name(name):
                persons.append({
                    "name_native": name,
                    "name_latin": None,
                    "aliases": [],
                    "current_position": position,
                    "service_or_agency": None,
                    "rank_or_grade": None,
                    "thematic_keywords": [],
                })

        return {"persons": persons, "organizations": orgs, "edges": edges}

    # ------------------------------------------------------------------
    # Narrative detection (KCNA, Rodong Sinmun)
    # ------------------------------------------------------------------
    def _detect_narrative_text(self, soup: BeautifulSoup) -> bool:
        paragraphs = soup.find_all("p")
        long_paragraphs = [p for p in paragraphs if len(p.get_text(strip=True)) > 200]
        return len(long_paragraphs) > 0

    # ------------------------------------------------------------------
    # Ambiguity detection
    # ------------------------------------------------------------------
    def _detect_ambiguity(self, persons: List[Dict[str, Any]]) -> bool:
        for p in persons:
            if not p.get("current_position"):
                return True
        return False

    # ------------------------------------------------------------------
    # Korean name heuristic
    # ------------------------------------------------------------------
    def _is_korean_name(self, text: str) -> bool:
        """
        Detect Korean names:
          - Typically 2–4 Hangul syllables
          - Family name first (김정은, 리병철, 박정천)
        """
        if not text:
            return False

        parts = text.split()
        if len(parts) != 1:
            return False

        # Hangul block detection
        return all("\uAC00" <= ch <= "\uD7A3" for ch in text)
