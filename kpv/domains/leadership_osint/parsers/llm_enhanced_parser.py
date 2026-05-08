from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger


class LLMEnhancedParser:
    """
    Hybrid parser that combines:
      - classical structured parsing (HTML/JSON extraction)
      - LLM semantic extraction (entities, relationships, events)

    Responsibilities:
      - run classical parser first (deterministic)
      - detect missing or ambiguous fields
      - invoke LLM extractor only when needed
      - merge structured + LLM results
      - validate and return normalized records
      - log every step for auditability
    """

    def __init__(
        self,
        country_code: str,
        classical_parser: Any,
        llm_extractor: Any,
        data_root: str = "./kpv_data",
    ):
        self.country_code = country_code.upper()
        self.classical = classical_parser
        self.llm = llm_extractor

        self.logger = get_logger(f"KPV.Parser.{self.country_code}.Hybrid", data_root)
        self.logger.info("Initialized LLMEnhancedParser")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse_document(self, html: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse a single document using hybrid logic.
        Returns:
          {
            "persons": [...],
            "organizations": [...],
            "edges": [...],
            "events": [...]
          }
        """
        self.logger.info(f"Parsing document (len={len(html)} chars)")

        # --------------------------------------------------------------
        # Step 1: Classical structured extraction
        # --------------------------------------------------------------
        structured = self._run_classical_parser(html)

        # --------------------------------------------------------------
        # Step 2: Determine if LLM extraction is needed
        # --------------------------------------------------------------
        needs_llm = self._needs_llm(structured)

        if needs_llm:
            self.logger.info("Structured extraction incomplete → invoking LLM")
            llm_results = self._run_llm_extractor(html)
        else:
            self.logger.info("Structured extraction sufficient → skipping LLM")
            llm_results = {"persons": [], "organizations": [], "edges": [], "events": []}

        # --------------------------------------------------------------
        # Step 3: Merge structured + LLM results
        # --------------------------------------------------------------
        merged = self._merge_results(structured, llm_results)

        # --------------------------------------------------------------
        # Step 4: Final validation + normalization
        # --------------------------------------------------------------
        normalized = self._normalize_output(merged)

        self.logger.info(
            f"Document parsed: persons={len(normalized['persons'])}, "
            f"orgs={len(normalized['organizations'])}, "
            f"edges={len(normalized['edges'])}, "
            f"events={len(normalized['events'])}"
        )

        return normalized

    # ------------------------------------------------------------------
    # Classical parser
    # ------------------------------------------------------------------
    def _run_classical_parser(self, html: str) -> Dict[str, Any]:
        """
        Run deterministic extraction first.
        """
        try:
            return self.classical.parse(html)
        except Exception as e:
            self.logger.error(f"Classical parser failed: {e}")
            return {
                "persons": [],
                "organizations": [],
                "edges": [],
                "events": [],
            }

    # ------------------------------------------------------------------
    # LLM extractor
    # ------------------------------------------------------------------
    def _run_llm_extractor(self, text: str) -> Dict[str, Any]:
        """
        Run LLM extraction for entities, relationships, and events.
        """
        results = {
            "persons": [],
            "organizations": [],
            "edges": [],
            "events": [],
        }

        # Entities
        try:
            ent = self.llm.extract_entities(text)
            if ent.success:
                results["persons"] = ent.data.get("persons", [])
                results["organizations"] = ent.data.get("organizations", [])
            else:
                self.logger.warning(f"LLM entity extraction failed: {ent.error}")
        except Exception as e:
            self.logger.error(f"LLM entity extraction exception: {e}")

        # Relationships
        try:
            rel = self.llm.extract_relationships(text)
            if rel.success:
                results["edges"] = rel.data.get("edges", [])
            else:
                self.logger.warning(f"LLM relationship extraction failed: {rel.error}")
        except Exception as e:
            self.logger.error(f"LLM relationship extraction exception: {e}")

        # Events
        try:
            ev = self.llm.extract_events(text)
            if ev.success:
                results["events"] = ev.data.get("events", [])
            else:
                self.logger.warning(f"LLM event extraction failed: {ev.error}")
        except Exception as e:
            self.logger.error(f"LLM event extraction exception: {e}")

        return results

    # ------------------------------------------------------------------
    # Determine if LLM is needed
    # ------------------------------------------------------------------
    def _needs_llm(self, structured: Dict[str, Any]) -> bool:
        """
        Decide whether to invoke the LLM based on structured extraction completeness.
        """
        # If no persons or orgs found → definitely need LLM
        if not structured.get("persons") and not structured.get("organizations"):
            return True

        # If text is narrative (classical parser flags it)
        if structured.get("narrative_text_detected"):
            return True

        # If classical parser marked ambiguity
        if structured.get("ambiguous_fields"):
            return True

        return False

    # ------------------------------------------------------------------
    # Merge structured + LLM results
    # ------------------------------------------------------------------
    def _merge_results(
        self,
        structured: Dict[str, Any],
        llm: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge structured and LLM results with priority rules:
          - structured data wins when fields conflict
          - LLM fills gaps
        """
        merged = {
            "persons": [],
            "organizations": [],
            "edges": [],
            "events": [],
        }

        # Persons
        merged["persons"] = structured.get("persons", []) + [
            p for p in llm.get("persons", [])
            if not self._is_duplicate_person(p, structured.get("persons", []))
        ]

        # Organizations
        merged["organizations"] = structured.get("organizations", []) + [
            o for o in llm.get("organizations", [])
            if not self._is_duplicate_org(o, structured.get("organizations", []))
        ]

        # Edges
        merged["edges"] = structured.get("edges", []) + llm.get("edges", [])

        # Events
        merged["events"] = structured.get("events", []) + llm.get("events", [])

        return merged

    # ------------------------------------------------------------------
    # Duplicate detection helpers
    # ------------------------------------------------------------------
    def _is_duplicate_person(self, new: Dict[str, Any], existing: List[Dict[str, Any]]) -> bool:
        for p in existing:
            if (
                p.get("name_native") == new.get("name_native")
                or p.get("name_latin") == new.get("name_latin")
            ):
                return True
        return False

    def _is_duplicate_org(self, new: Dict[str, Any], existing: List[Dict[str, Any]]) -> bool:
        for o in existing:
            if o.get("name") == new.get("name"):
                return True
        return False

    # ------------------------------------------------------------------
    # Final normalization
    # ------------------------------------------------------------------
    def _normalize_output(self, merged: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all required keys exist and types are correct.
        """
        return {
            "persons": merged.get("persons", []),
            "organizations": merged.get("organizations", []),
            "edges": merged.get("edges", []),
            "events": merged.get("events", []),
        }
