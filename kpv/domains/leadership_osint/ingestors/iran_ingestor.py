from __future__ import annotations

from typing import Dict, Any

from .base_ingestor import BaseIngestor
from ..utils.logger import get_logger


class IranIngestor(BaseIngestor):
    """
    Iran-specific ingestor.

    Responsibilities (country-specific only):
      - normalize Persian names (given + father's name + family name)
      - handle clerical titles (Ayatollah, Hojjatoleslam)
      - normalize IRGC ranks
      - map ministries, services, and bonyads
      - normalize SOEs (NIOC, NDFI, MAPNA)

    All generic ingestion logic is inherited from BaseIngestor:
      - schema validation
      - identity resolution
      - dataset merging
      - diff computation
      - deterministic ID generation
    """

    country_code = "IR"

    def __init__(self, data_root: str = "./kpv_data"):
        super().__init__(country_code="IR", data_root=data_root)
        self.logger = get_logger("KPV.Ingest.IR", data_root)
        self.logger.info("Initialized IranIngestor")

    # ------------------------------------------------------------------
    # Person normalization
    # ------------------------------------------------------------------
    def normalize_person(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Persian person records.
        """
        p = super().normalize_person(p)

        # Remove clerical titles
        name = p.get("name_native", "")
        for title in ["آیت‌الله", "حجت‌الاسلام", "سردار"]:
            if name.startswith(title):
                name = name.replace(title, "").strip()
        p["name_native"] = name

        # Persian naming: given + father's name + family name
        parts = name.split()
        if len(parts) == 3:
            given, father, family = parts
            p["given_name"] = given
            p["fathers_name"] = father
            p["surname"] = family

        # IRGC rank normalization
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
        Normalize Iranian organizations.
        """
        o = super().normalize_org(o)

        name = o.get("name", "")

        # Bonyads
        if "بنیاد" in name:
            o["type"] = "Bonyad"
            o["parent_org"] = "Government of the Islamic Republic of Iran"

        # SOEs
        if any(k in name for k in ["نفت", "NIOC", "MAPNA", "NDFI"]):
            o["type"] = "SOE"
            o["parent_org"] = "Government of the Islamic Republic of Iran"

        return o

    # ------------------------------------------------------------------
    # IRGC rank normalization
    # ------------------------------------------------------------------
    def _normalize_rank(self, rank: str) -> str:
        rank = rank.lower()

        mapping = {
            "سردار": "Sardar (General Officer)",
            "سرلشکر": "Major General",
            "سپهبد": "Lieutenant General",
            "سرتیپ دوم": "Brigadier General (2nd Class)",
            "سرتیپ": "Brigadier General",
            "سرهنگ": "Colonel",
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
            "سپاه": "IRGC",
            "سپاه پاسداران": "IRGC",
            "نیروی قدس": "IRGC-Quds",
            "سازمان اطلاعات سپاه": "IRGC-Intelligence",
            "ارتش": "Artesh",
            "نیروی انتظامی": "LEF",
            "وزارت اطلاعات": "MOIS",
            "وزارت دفاع": "MODAFL",
            "وزارت کشور": "Ministry of Interior",
        }

        for k, v in mapping.items():
            if k in agency:
                return v

        return agency
