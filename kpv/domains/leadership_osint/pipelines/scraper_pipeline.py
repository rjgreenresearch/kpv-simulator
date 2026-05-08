from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from ..utils.storage import StorageManager
from ..utils.diff import compute_diff


class ScraperPipeline:
    """
    Top-level orchestrator for the OSINT ingestion workflow.

    Pipeline:
      1. Scraper fetches raw HTML/text from URLs
      2. Hybrid parser extracts structured + LLM-enhanced entities
      3. Ingestor normalizes, resolves identities, updates dataset
      4. StorageManager writes snapshots
      5. Diff engine computes deltas
      6. Full logging for auditability

    This class is country-agnostic and DRY by design.
    """

    def __init__(
        self,
        country_code: str,
        scraper: Any,
        parser: Any,
        ingestor: Any,
        storage: Optional[StorageManager] = None,
        data_root: str = "./kpv_data",
    ):
        self.country_code = country_code.upper()
        self.scraper = scraper
        self.parser = parser
        self.ingestor = ingestor

        self.storage = storage or StorageManager(data_root)
        self.data_root = data_root

        self.logger = get_logger(f"KPV.Pipeline.{self.country_code}", data_root)
        self.logger.info("Initialized ScraperPipeline")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """
        Execute the full ingestion pipeline for a country.
        Returns:
          {
            "updated_dataset": {...},
            "diff": {...},
            "snapshot_path": "..."
          }
        """
        self.logger.info(f"Starting pipeline for {self.country_code}")

        # --------------------------------------------------------------
        # Step 1: Load existing dataset
        # --------------------------------------------------------------
        existing = self._load_existing_dataset()

        # --------------------------------------------------------------
        # Step 2: Scrape all configured URLs
        # --------------------------------------------------------------
        raw_docs = self._scrape_all()

        # --------------------------------------------------------------
        # Step 3: Parse documents (hybrid structured + LLM)
        # --------------------------------------------------------------
        parsed_records = self._parse_all(raw_docs)

        # --------------------------------------------------------------
        # Step 4: Normalize + resolve identities + update dataset
        # --------------------------------------------------------------
        updated_dataset = self._ingest(parsed_records, existing)

        # --------------------------------------------------------------
        # Step 5: Compute diff
        # --------------------------------------------------------------
        diff = compute_diff(existing, updated_dataset)

        # --------------------------------------------------------------
        # Step 6: Write snapshot
        # --------------------------------------------------------------
        snapshot_path = self.storage.write_snapshot(
            country_code=self.country_code,
            dataset=updated_dataset,
        )

        self.logger.info(
            f"Pipeline complete for {self.country_code}: "
            f"persons={len(updated_dataset.get('persons', []))}, "
            f"orgs={len(updated_dataset.get('organizations', []))}, "
            f"edges={len(updated_dataset.get('edges', []))}"
        )

        return {
            "updated_dataset": updated_dataset,
            "diff": diff,
            "snapshot_path": snapshot_path,
        }

    # ------------------------------------------------------------------
    # Step 1: Load existing dataset
    # ------------------------------------------------------------------
    def _load_existing_dataset(self) -> Dict[str, Any]:
        try:
            dataset = self.storage.load_latest(self.country_code)
            if dataset:
                self.logger.info("Loaded existing dataset")
                return dataset
        except Exception as e:
            self.logger.error(f"Failed to load existing dataset: {e}")

        self.logger.warning("No existing dataset found; starting fresh")
        return {"persons": [], "organizations": [], "edges": []}

    # ------------------------------------------------------------------
    # Step 2: Scrape all URLs
    # ------------------------------------------------------------------
    def _scrape_all(self) -> List[Dict[str, Any]]:
        docs = []
        urls = self.scraper.get_target_urls()

        self.logger.info(f"Scraping {len(urls)} URLs")

        for url in urls:
            try:
                html = self.scraper.fetch(url)
                docs.append({"url": url, "html": html})
            except Exception as e:
                self.logger.error(f"Failed to scrape {url}: {e}")

        return docs

    # ------------------------------------------------------------------
    # Step 3: Parse all documents
    # ------------------------------------------------------------------
    def _parse_all(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        parsed = []

        for doc in docs:
            try:
                result = self.parser.parse_document(doc["html"], url=doc["url"])
                parsed.append(result)
            except Exception as e:
                self.logger.error(f"Parser failed for {doc['url']}: {e}")

        return parsed

    # ------------------------------------------------------------------
    # Step 4: Ingest parsed records
    # ------------------------------------------------------------------
    def _ingest(
        self,
        parsed_records: List[Dict[str, Any]],
        existing: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Flatten parsed records and feed into the ingestor.
        """
        combined = {
            "persons": [],
            "organizations": [],
            "edges": [],
        }

        for record in parsed_records:
            combined["persons"].extend(record.get("persons", []))
            combined["organizations"].extend(record.get("organizations", []))
            combined["edges"].extend(record.get("edges", []))

        # Normalize + resolve identities + update dataset
        normalized = self.ingestor.normalize(combined)
        resolved = self.ingestor.resolve_identities(normalized, existing)
        updated = self.ingestor.update_dataset(resolved, existing)

        return updated
