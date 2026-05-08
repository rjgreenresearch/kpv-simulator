from __future__ import annotations

from typing import Any, Dict, List

from bs4 import BeautifulSoup

from ..utils.logger import get_logger


class IranClassicalParser:
    """
    Deterministic HTML parser for Iranian leadership sources.

    Responsibilities:
      - Extract structured data from:
          * Supreme Leader’s Office
          * Presidency + ministries
          * Majlis + Judiciary
          * IRGC, Artesh, LEF leadership tables
          * Bonyad + SOE leadership blocks
      - Identify Persian names (given + father's name + family name)
      - Detect clerical titles (Ayatollah, Hojjatoleslam)
      - Detect narrative text (IRNA, Tasnim, Fars)
      - Detect ambiguous fields to trigger LLM fallback
    """

    def __init__(self, data_root: str = "./kpv_data"):
        self.data_root = data_root
        self.logger = get_logger("KPV.Parser.IR.Classical", data_root)
        self.logger.info("Initialized IranClassicalParser")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse(self, html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")

        persons = []
        orgs = []
        edges = []

        # 1. Leadership tables (IRGC, Artesh, ministries)
        table_results = self._parse_tables(soup)
        persons.extend(table_results["persons"])
        orgs.extend(table_results["organizations"])
        edges.extend(table_results["edges"])

        # 2. Leadership lists (Supreme Leader’s Office, Majlis, Judiciary)
        list_results = self._parse_leadership_lists(soup)
        persons.extend(list_results["persons"])
        orgs.extend(list_results["organizations"])
        edges.extend(list_results["edges"])

        # 3. Bonyad + SOE leadership blocks
        soe_results = self._parse_soe_blocks(soup)
        persons.extend(soe_results["persons"])
        orgs.extend(soe_results["organizations"])
        edges.extend(soe_results["edges"])

        # 4. Narrative detection (IRNA, Tasnim, Fars)
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
    # Leadership tables (IRGC, Artesh, ministries)
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

                if self._is_persian_name(name):
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
    # Leadership lists (Supreme Leader’s Office, Majlis, Judiciary)
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

            if self._is_persian_name(name):
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
    # Bonyad + SOE leadership blocks
    # ------------------------------------------------------------------
    def _parse_soe_blocks(self, soup: BeautifulSoup) -> Dict[str, Any]:
        persons = []
        orgs = []
        edges = []

        for div in soup.find_all(["div", "p"]):
            text = div.get_text(strip=True)
            if not text:
                continue

            if any(k in text for k in ["بنیاد", "شرکت", "گروه", "نفت", "انرژی"]):
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

                if self._is_persian_name(name):
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
    # Narrative detection (IRNA, Tasnim, Fars)
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
    # Persian name heuristic
    # ------------------------------------------------------------------
    def _is_persian_name(self, text: str) -> bool:
        """
        Detect Persian names:
          - Typically 2–3 words
          - Often includes father's name as middle component
          - Clerical titles (Ayatollah, Hojjatoleslam) may precede name
        """
        if not text:
            return False

        # Remove clerical titles
        for title in ["آیت‌الله", "حجت‌الاسلام", "سردار"]:
            if text.startswith(title):
                text = text.replace(title, "").strip()

        parts = text.split()
        if len(parts) < 2 or len(parts) > 4:
            return False

        # Persian script detection
        return all(
            all("\u0600" <= ch <= "\u06FF" for ch in part)
            for part in parts
        )
