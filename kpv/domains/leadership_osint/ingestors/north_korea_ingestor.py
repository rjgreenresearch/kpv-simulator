from __future__ import annotations

from typing import Dict, Any

from .base_ingestor import BaseIngestor
from ..utils.logger import get_logger


class NorthKoreaIngestor(BaseIngestor):
    """
    DPRK-specific ingestor.

    Responsibilities (country-specific only):
      - normalize Korean names (family name first)
      - normalize WPK titles
      - normalize KPA ranks
      - map ministries, commissions, and security organs
      - normalize DPRK SOEs
    """

    country_code = "KP"

    def __init__(self, data_root: str = "./kpv_data"):
        super().__init__(country_code="KP", data_root=data_root)
        self.logger = get_logger("KPV.Ingest.KP", data_root)
        self.logger.info("Initialized NorthKoreaIngestor")

    # ------------------------------------------------------------------
    # Person normalization
    # ------------------------------------------------------------------
    def normalize_person(self, p: Dict[str, Any]) -> Dict[str, Any]:
        p = super().normalize_person(p)

        name = p.get("name_native", "")

        # Remove honorifics (동지, 원수, 장군)
        for title in ["동지", "원수", "대원수", "장군"]:
            if name.startswith(title):
                name = name.replace(title, "").strip()

        # Korean names: family name first, usually 2–4 Hangul syllables
        if name and 2 <= len(name) <= 4:
            family = name[0]
            given = name[1:]
            p["surname"] = family
            p["given_name"] = given

        # WPK title normalization
        title = p.get("current_position", "")
        p["current_position"] = self._normalize_wpk_title(title)

        # KPA rank normalization
        rank = p.get("rank_or_grade", "")
        p["rank_or_grade"] = self._normalize_kpa_rank(rank)

        # Ministry / agency mapping
        agency = p.get("service_or_agency", "")
        p["service_or_agency"] = self._map_agency(agency)

        return p

    # ------------------------------------------------------------------
    # Organization normalization
    # ------------------------------------------------------------------
    def normalize_org(self, o: Dict[str, Any]) -> Dict[str, Any]:
        o = super().normalize_org(o)

        name = o.get("name", "")

        # DPRK SOEs (economic ministries + industrial groups)
        if any(k in name for k in ["공장", "기업소", "연합기업소", "총국"]):
            o["type"] = "SOE"
            o["parent_org"] = "Cabinet of the DPRK"

        # WPK bodies
        if "조선로동당" in name or "당 중앙위원회" in name:
            o["type"] = "WPK Body"
            o["parent_org"] = "Workers' Party of Korea"

        return o

    # ------------------------------------------------------------------
    # WPK title normalization
    # ------------------------------------------------------------------
    def _normalize_wpk_title(self, title: str) -> str:
        title = title.lower()

        mapping = {
            "조선로동당 위원장": "Chairman of the Workers' Party of Korea",
            "국무위원장": "President of the State Affairs Commission",
            "국무위원회 부위원장": "Vice Chairman of the State Affairs Commission",
            "국무위원회 위원": "Member of the State Affairs Commission",
            "내각 총리": "Premier of the Cabinet",
            "부총리": "Vice Premier",
            "상": "Minister",
            "부상": "Vice Minister",
        }

        for k, v in mapping.items():
            if k in title:
                return v

        return title

    # ------------------------------------------------------------------
    # KPA rank normalization
    # ------------------------------------------------------------------
    def _normalize_kpa_rank(self, rank: str) -> str:
        rank = rank.lower()

        mapping = {
            "대원수": "Grand Marshal",
            "원수": "Marshal",
            "차수": "Vice Marshal",
            "대장": "General",
            "상장": "Colonel General",
            "중장": "Lieutenant General",
            "소장": "Major General",
            "대좌": "Senior Colonel",
            "상좌": "Colonel",
            "중좌": "Lieutenant Colonel",
            "소좌": "Major",
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
            "조선로동당": "Workers' Party of Korea",
            "국무위원회": "State Affairs Commission",
            "내각": "Cabinet",
            "인민무력성": "Ministry of Defence",
            "총참모부": "KPA General Staff",
            "총정치국": "KPA General Political Bureau",
            "국가보위성": "State Security Department",
            "인민보안성": "Ministry of Social Security",
        }

        for k, v in mapping.items():
            if k in agency:
                return v

        return agency
