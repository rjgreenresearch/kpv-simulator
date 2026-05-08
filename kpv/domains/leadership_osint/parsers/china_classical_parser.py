from __future__ import annotations

from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from ..utils.logger import get_logger


class ChinaClassicalParser:
    """
    Deterministic HTML parser for PRC leadership sources.

    Responsibilities:
      - Extract structured data from:
          * tables
          * leadership directories
          * ministry pages
          * PLA Daily org charts
      - Identify names, positions, organizations
      - Detect narrative text (to trigger LLM fallback)
      - Produce structured output:
          {
            "persons": [...],
            "organizations": [...],
            "edges": [...],
            "events": [...],
            "narrative_text_detected": bool,
            "ambiguous_fields": bool
          }
    """

    def __init__(self, data_root: str = "./kpv_data"):
        self.data_root = data_root
        self.logger = get_logger("KPV.Parser.CN.Classical", data_root)
        self.logger.info("Initialized ChinaClassicalParser")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse(self, html: str) -> Dict[str, Any]:
        """
        Parse HTML using deterministic rules.
        """
        soup = BeautifulSoup(html, "html.parser")

        persons = []
        orgs = []
        edges = []

        ambiguous = False
        narrative_detected = False

        # --------------------------------------------------------------
        # 1. Extract leadership tables (common on gov.cn)
        # --------------------------------------------------------------
        table_results = self._parse_tables(soup)
        persons.extend(table_results["persons"])
        orgs.extend(table_results["organizations"])
        edges.extend(table_results["edges"])

        # --------------------------------------------------------------
        # 2. Extract leadership lists (common on mod.gov.cn, xinhuanet)
        # --------------------------------------------------------------
        list_results = self._parse_leadership_lists(soup)
        persons.extend(list_results["persons"])
        orgs.extend(list_results["organizations"])
        edges.extend(list_results["edges"])

        # --------------------------------------------------------------
        # 3. Detect narrative text (to trigger LLM fallback)
        # --------------------------------------------------------------
        narrative_detected = self._detect_narrative_text(soup)

        # --------------------------------------------------------------
        # 4. Detect ambiguous fields (missing positions, unclear orgs)
        # --------------------------------------------------------------
        ambiguous = self._detect_ambiguity(persons)

        # --------------------------------------------------------------
        # 5. Return structured output
        # --------------------------------------------------------------
        return {
            "persons": persons,
            "organizations": orgs,
            "edges": edges,
            "events": [],  # classical parser rarely extracts events
            "narrative_text_detected": narrative_detected,
            "ambiguous_fields": ambiguous,
        }

    # ------------------------------------------------------------------
    # Leadership tables
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

                # Heuristic: first column = name, second = position
                name = cols[0]
                position = cols[1]

                if self._is_chinese_name(name):
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
    # Leadership lists
    # ------------------------------------------------------------------
    def _parse_leadership_lists(self, soup: BeautifulSoup) -> Dict[str, Any]:
        persons = []
        orgs = []
        edges = []

        # Look for <li> patterns like:
        #   李尚福  国务委员、国防部长
        for li in soup.find_all("li"):
            text = li.get_text(strip=True)
            if not text:
                continue

            # Split on whitespace or punctuation
            parts = text.replace("：", ":").split(":")
            if len(parts) < 2:
                continue

            name = parts[0].strip()
            position = parts[1].strip()

            if self._is_chinese_name(name):
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
    # Narrative detection
    # ------------------------------------------------------------------
    def _detect_narrative_text(self, soup: BeautifulSoup) -> bool:
        """
        Detect long paragraphs typical of Xinhua, PLA Daily, etc.
        """
        paragraphs = soup.find_all("p")
        long_paragraphs = [p for p in paragraphs if len(p.get_text(strip=True)) > 200]

        return len(long_paragraphs) > 0

    # ------------------------------------------------------------------
    # Ambiguity detection
    # ------------------------------------------------------------------
    def _detect_ambiguity(self, persons: List[Dict[str, Any]]) -> bool:
        """
        Detect missing positions or unclear roles.
        """
        for p in persons:
            if not p.get("current_position"):
                return True
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _is_chinese_name(self, text: str) -> bool:
        """
        Simple heuristic: Chinese names are usually 2–3 characters.
        """
        if not text:
            return False

        if 2 <= len(text) <= 4:
            # Check if characters are in CJK range
            return all("\u4e00" <= ch <= "\u9fff" for ch in text)

        return False
