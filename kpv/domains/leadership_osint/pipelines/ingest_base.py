from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path
import json
import jsonschema

from ..utils.logger import get_logger


class BaseIngestor(ABC):
    """
    Abstract base class for all country-specific OSINT ingestors.
    Provides:
      - schema validation
      - logging
      - dataset lifecycle hooks
    """

    def __init__(self, country_code: str, data_root: str = "./kpv_data"):
        self.country_code = country_code.upper()
        self.data_root = Path(data_root).resolve()
        self.logger = get_logger(f"KPV.Ingest.{self.country_code}", data_root)

        # Schemas injected by update_country.py
        self.person_schema = None
        self.org_schema = None
        self.edge_schema = None

        self.logger.info(f"BaseIngestor initialized for {self.country_code}")

    # ------------------------------------------------------------
    # Abstract ingestion steps
    # ------------------------------------------------------------
    @abstractmethod
    def fetch_raw(self) -> List[Any]:
        pass

    @abstractmethod
    def normalize(self, raw: List[Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def resolve_identities(
        self,
        normalized: List[Dict[str, Any]],
        existing: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_dataset(
        self,
        resolved: Dict[str, Any],
        existing: Dict[str, Any]
    ) -> Dict[str, Any]:
        pass

    # ------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------
    def validate_person(self, person: Dict[str, Any]):
        if not self.person_schema:
            return
        try:
            jsonschema.validate(person, self.person_schema)
        except Exception as e:
            self.logger.error(f"Person validation failed: {e}")
            raise

    def validate_org(self, org: Dict[str, Any]):
        if not self.org_schema:
            return
        try:
            jsonschema.validate(org, self.org_schema)
        except Exception as e:
            self.logger.error(f"Organization validation failed: {e}")
            raise

    def validate_edge(self, edge: Dict[str, Any]):
        if not self.edge_schema:
            return
        try:
            jsonschema.validate(edge, self.edge_schema)
        except Exception as e:
            self.logger.error(f"Edge validation failed: {e}")
            raise
