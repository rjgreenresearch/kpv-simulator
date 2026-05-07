from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseIngestor(ABC):
    """
    Abstract base class for all country-specific OSINT ingestion modules.
    """

    @abstractmethod
    def fetch_raw(self) -> List[Any]:
        """
        Fetch raw OSINT data from external sources.
        """
        pass

    @abstractmethod
    def normalize(self, raw: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert raw OSINT hits into normalized person/org/edge dicts.
        """
        pass

    @abstractmethod
    def resolve_identities(
        self,
        normalized: List[Dict[str, Any]],
        existing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Match normalized items to existing dataset and merge or create new entries.
        """
        pass

    @abstractmethod
    def update_dataset(
        self,
        resolved: Dict[str, Any],
        existing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Produce the final updated dataset.
        """
        pass
