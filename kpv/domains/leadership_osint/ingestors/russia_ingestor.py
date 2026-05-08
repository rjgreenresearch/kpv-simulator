from __future__ import annotations

from typing import Dict, Any, List

from .base_ingestor import BaseIngestor
from ..utils.logger import get_logger


class RussiaIngestor(BaseIngestor):
    """
    Russia-specific ingestor.

    Responsibilities (country-specific only):
      - normalize Russian names (given + patronymic + surname)
      - normalize ranks (генерал-полковник → Colonel General)
      - map ministries, services, and SOEs
      - apply Russian-specific heuristics before identity resolution

    All generic ingestion logic is inherited from BaseIngestor:
      - schema validation
      - identity resolution
      - dataset merging
      - diff computation
      - deterministic ID generation
    """

    country_code = "RU"

    def __init__(self, data_root: str = "./kpv_data"):
        super().__init__(country_code="RU", data_root=data_root)
        self.logger = get_logger("KPV.Ingest.RU", data_root)
        self.logger.info("Initialized RussiaIngestor")

    # ------------------------------------------------------------------
    # Person normalization
    # ------------------------------------------------------------------
    def normalize_person(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Russian person records.
        """
        p = super().normalize_person(p)

        # Patronymic handling
        if p.get("name_native"):
            parts = p["name_native"].split()
            if len(parts) == 3:
                given, patronymic, surname = parts
                p["given_name"] = given
                p["patronymic"] = patronymic
                p["surname"] = surname

        # Rank normalization
        rank = p.get("rank_or_grade", "")
        p["rank_or_grade"] = self._normalize_rank(rank)

        # Ministry / service mapping
        agency = p.get("service_or_agency", "")
        p["service_or_agency"] = self._map_agency(agency)

        return p

    # ------------------------------------------------------------------
    # Organization normalization
    # ------------------------------------------------------------------
    def normalize_org(self, o: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Russian organizations.
        """
        o = super().normalize_org(o)

        name = o.get("name", "")

        # SOE mapping
        if "Газпром" in name:
            o["type"] = "SOE"
            o["parent_org"] = "Government of the Russian Federation"

        if "Роснефть" in name:
            o["type"] = "SOE"
            o["parent_org"] = "Government of the Russian Federation"

        if "Ростех" in name or "Rostec" in name:
            o["type"] = "SOE"
            o["parent_org"] = "Government of the Russian Federation"

        return o

    # ------------------------------------------------------------------
    # Rank normalization table
    # ------------------------------------------------------------------
    def _normalize_rank(self, rank: str) -> str:
        rank = rank.lower()

        mapping = {
            "генерал армии": "Army General",
            "генерал-полковник": "Colonel General",
            "генерал-лейтенант": "Lieutenant General",
            "генерал-майор": "Major General",
            "полковник": "Colonel",
            "подполковник": "Lieutenant Colonel",
            "майор": "Major",
        }

        for k, v in mapping.items():
            if k in rank:
                return v

        return rank

    # ------------------------------------------------------------------
    # Agency mapping
    # ------------------------------------------------------------------
    def _map_agency(self, agency: str) -> str:
        agency = agency.lower()

        mapping = {
            "министерство обороны": "Ministry of Defence",
            "минобороны": "Ministry of Defence",
            "фсб": "FSB",
            "федеральная служба безопасности": "FSB",
            "свр": "SVR",
            "служба внешней разведки": "SVR",
            "гру": "GRU",
            "главное разведывательное управление": "GRU",
            "росгвардия": "Rosgvardia",
        }

        for k, v in mapping.items():
            if k in agency:
                return v

        return agency
