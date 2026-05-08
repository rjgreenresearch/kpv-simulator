from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup

from ..utils.logger import get_logger


class RussiaClassicalParser:
    """
    Deterministic HTML parser for Russian leadership sources.

    Responsibilities:
      - Extract structured data from:
          * Kremlin.ru leadership blocks
          * Government.ru ministry pages
          * Duma.gov.ru / Council.gov.ru lists
          * MOD leadership tables (mil.ru)
          * SOE leadership sections (Gazprom, Rosneft, Rostec)
      - Identify Russian names (given + patronymic + surname)
      - Detect narrative text (TASS, RIA, Interfax, RG)
      - Detect ambiguous fields to trigger LLM fallback
    """

    def __init__(self, data_root: str = "./kpv_data"):
        self.data_root = data_root
        self.logger = get_logger("KPV.Parser.RU.Classical", data_root)
        self.logger.info("Initialized RussiaClassicalParser")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse(self, html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")

        persons = []
        orgs = []
        edges = []

        # 1. Leadership tables (MOD, ministries)
        table_results = self._parse_tables(soup)
        persons.extend(table_results["persons"])
        orgs.extend(table_results["organizations"])
        edges.extend(table_results["edges"])

        # 2. Leadership lists (Kremlin, Duma, Council)
        list_results = self._parse_leadership_lists(soup)
        persons.extend(list_results["persons"])
        orgs.extend(list_results["organizations"])
        edges.extend(list_results["edges"])

        # 3. SOE leadership blocks
        soe_results = self._parse_soe_blocks(soup)
        persons.extend(soe_results["persons"])
        orgs.extend(soe_results["organizations"])
        edges.extend(soe_results["edges"])

        # 4. Narrative detection (TASS, RIA, Interfax, RG)
        narrative_detected = self._detect_narrative_text(soup)

        # 5. Ambiguity detection
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
    # Leadership tables (MOD, ministries)
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

                if self._is_russian_name(name):
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
    # Leadership lists (Kremlin, Duma, Council)
    # ------------------------------------------------------------------
    def _parse_leadership_lists(self, soup: BeautifulSoup) -> Dict[str, Any]:
        persons = []
        orgs = []
        edges = []

        for li in soup.find_all("li"):
            text = li.get_text(strip=True)
            if not text:
                continue

            # Split on colon or dash
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

            if self._is_russian_name(name):
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
    # SOE leadership blocks (Gazprom, Rosneft, Rostec)
    # ------------------------------------------------------------------
    def _parse_soe_blocks(self, soup: BeautifulSoup) -> Dict[str, Any]:
        persons = []
        orgs = []
        edges = []

        # Look for patterns like:
        #   Алексей Миллер — Председатель Правления ПАО «Газпром»
        for div in soup.find_all(["div", "p"]):
            text = div.get_text(strip=True)
            if not text:
                continue

            if "ПАО" in text or "АО" in text or "Госкорпорация" in text:
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

                if self._is_russian_name(name):
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
    # Narrative detection (TASS, RIA, Interfax, RG)
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
    # Russian name heuristic
    # ------------------------------------------------------------------
    def _is_russian_name(self, text: str) -> bool:
        """
        Detect Russian names:
          - Typically 2–3 words
          - Patronymic often ends with -ович, -евич, -овна, -евна
        """
        if not text:
            return False

        parts = text.split()
        if len(parts) < 2 or len(parts) > 4:
            return False

        # Patronymic detection
        if any(
            p.endswith(("ович", "евич", "овна", "евна"))
            for p in parts
        ):
            return True

        # Fallback: Cyrillic + 2–3 words
        return all(
            all("\u0400" <= ch <= "\u04FF" for ch in part)
            for part in parts
        )