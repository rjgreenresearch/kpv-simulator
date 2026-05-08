from __future__ import annotations

from typing import Dict, Any

from .base_ingestor import BaseIngestor
from ..utils.logger import get_logger


class ChinaIngestor(BaseIngestor):
    """
    China-specific ingestor.

    Responsibilities (country-specific only):
      - normalize Chinese names (family name first → given name)
      - normalize CCP titles and ranks
      - normalize PLA ranks
      - map ministries, commissions, and SOEs (SASAC ecosystem)
      - apply China-specific heuristics before identity resolution

    All generic ingestion logic is inherited from BaseIngestor:
      - schema validation
      - identity resolution
      - dataset merging
      - diff computation
      - deterministic ID generation
    """

    country_code = "CN"

    def __init__(self, data_root: str = "./kpv_data"):
        super().__init__(country_code="CN", data_root=data_root)
        self.logger = get_logger("KPV.Ingest.CN", data_root)
        self.logger.info("Initialized ChinaIngestor")

    # ------------------------------------------------------------------
    # Person normalization
    # ------------------------------------------------------------------
    def normalize_person(self, p: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Chinese person records.
        """
        p = super().normalize_person(p)

        name = p.get("name_native", "")

        # Chinese names: family name first, usually 2–3 characters
        # Example: 习近平 → family: 习, given: 近平
        if name and len(name) >= 2 and len(name) <= 4:
            family = name[0]
            given = name[1:]
            p["surname"] = family
            p["given_name"] = given

        # CCP rank/title normalization
        title = p.get("current_position", "")
        p["current_position"] = self._normalize_ccp_title(title)

        # PLA rank normalization
        rank = p.get("rank_or_grade", "")
        p["rank_or_grade"] = self._normalize_pla_rank(rank)

        # Ministry / agency mapping
        agency = p.get("service_or_agency", "")
        p["service_or_agency"] = self._map_agency(agency)

        return p

    # ------------------------------------------------------------------
    # Organization normalization
    # ------------------------------------------------------------------
    def normalize_org(self, o: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Chinese organizations.
        """
        o = super().normalize_org(o)

        name = o.get("name", "")

        # SASAC SOEs
        if any(k in name for k in ["集团", "公司", "有限责任公司", "控股"]):
            o["type"] = "SOE"
            o["parent_org"] = "State-owned Assets Supervision and Administration Commission (SASAC)"

        # CCP bodies
        if "中央委员会" in name or "党中央" in name:
            o["type"] = "CCP Body"
            o["parent_org"] = "Communist Party of China"

        return o

    # ------------------------------------------------------------------
    # CCP title normalization
    # ------------------------------------------------------------------
    def _normalize_ccp_title(self, title: str) -> str:
        title = title.lower()

        mapping = {
            "总书记": "General Secretary of the CCP",
            "中央委员会总书记": "General Secretary of the CCP",
            "主席": "President of the PRC",
            "国务院总理": "Premier of the State Council",
            "常委": "Politburo Standing Committee Member",
            "政治局委员": "Politburo Member",
            "部长": "Minister",
            "副部长": "Vice Minister",
        }

        for k, v in mapping.items():
            if k in title:
                return v

        return title

    # ------------------------------------------------------------------
    # PLA rank normalization
    # ------------------------------------------------------------------
    def _normalize_pla_rank(self, rank: str) -> str:
        rank = rank.lower()

        mapping = {
            "上将": "General",
            "中将": "Lieutenant General",
            "少将": "Major General",
            "大校": "Senior Colonel",
            "上校": "Colonel",
            "中校": "Lieutenant Colonel",
            "少校": "Major",
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
            "中央军委": "Central Military Commission",
            "中共中央": "Communist Party of China",
            "国务院": "State Council",
            "外交部": "Ministry of Foreign Affairs",
            "国防部": "Ministry of National Defense",
            "公安部": "Ministry of Public Security",
            "国家安全部": "Ministry of State Security",
            "工信部": "Ministry of Industry and Information Technology",
            "发改委": "National Development and Reform Commission",
        }

        for k, v in mapping.items():
            if k in agency:
                return v

        return agency
