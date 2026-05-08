from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .country_profile import CountryLLMProfile


@dataclass
class NorthKoreaLLMProfile(CountryLLMProfile):
    """
    North Korea-specific LLM profile.

    Encodes:
      - Korean naming conventions (family name first)
      - WPK hierarchy and titles
      - KPA ranks and services
      - cabinet / state commission structures
      - state media narrative patterns (KCNA, Rodong Sinmun)
    """

    country_code: str = "KP"

    # ------------------------------------------------------------------
    # Language + Encoding
    # ------------------------------------------------------------------
    language: str = "ko"
    encoding: str = "utf-8"

    # ------------------------------------------------------------------
    # Naming conventions
    # ------------------------------------------------------------------
    # Korean names: family name first, usually 3 syllables (e.g., 김정은)
    name_order: str = "eastern"
    surname_first: bool = True

    common_surnames: List[str] = field(default_factory=lambda: [
        "김", "리", "박", "최", "정", "강", "조", "윤", "장", "임"
    ])

    honorifics: List[str] = field(default_factory=lambda: [
        "동지", "원수", "장군", "대원수"
    ])

    # ------------------------------------------------------------------
    # Titles, ranks, and political structures
    # ------------------------------------------------------------------
    common_titles: List[str] = field(default_factory=lambda: [
        "조선민주주의인민공화국 국무위원장",
        "조선로동당 위원장",
        "최고사령관",
        "국무위원회 위원",
        "내각 총리",
        "부총리",
        "상",
        "부상"
    ])

    # KPA rank patterns
    rank_patterns: List[str] = field(default_factory=lambda: [
        "대원수", "원수", "차수", "대장", "상장", "중장", "소장",
        "대좌", "상좌", "중좌", "소좌"
    ])

    # Political hierarchy (descending)
    political_hierarchy: List[str] = field(default_factory=lambda: [
        "조선민주주의인민공화국 국무위원장",
        "조선로동당 위원장",
        "국무위원회 부위원장",
        "국무위원회 위원",
        "내각 총리",
        "내각 부총리",
        "상",
        "부상"
    ])

    # ------------------------------------------------------------------
    # Organizational patterns
    # ------------------------------------------------------------------
    org_keywords: List[str] = field(default_factory=lambda: [
        "조선로동당", "국무위원회", "내각", "성", "위원회", "총국",
        "군", "사단", "여단", "연대"
    ])

    ministry_keywords: List[str] = field(default_factory=lambda: [
        "인민무력성", "국가보위성", "인민보안성", "외무성", "대외경제성"
    ])

    military_keywords: List[str] = field(default_factory=lambda: [
        "조선인민군", "인민무력성", "총참모부", "총정치국", "경비대",
        "국가보위성", "인민보안성"
    ])

    # ------------------------------------------------------------------
    # Security posture
    # ------------------------------------------------------------------
    bot_risk: str = "very_high"
    requires_proxy: bool = True
    requires_session: bool = False
    blocks_us_ips: bool = True

    # ------------------------------------------------------------------
    # Prompt tuning
    # ------------------------------------------------------------------
    max_entities: int = 80
    max_edges: int = 180
    max_events: int = 80

    # ------------------------------------------------------------------
    # Prompt templates (North Korea-specific)
    # ------------------------------------------------------------------
    entity_prompt_template: str = """
You are extracting structured leadership data from Korean-language text
about the DPRK (North Korea): party, state, military, security, and
state-media sources.

Follow these rules:
  - Korean names are usually family name first (e.g., 김정은).
  - Preserve full native (Korean) form and provide Latin transliteration.
  - Identify ranks, titles, and roles in:
      * Workers' Party of Korea (WPK)
      * State Affairs Commission (SAC)
      * Cabinet (Naegak)
      * Korean People's Army (KPA)
      * State Security and internal security organs
      * State media (KCNA, Rodong Sinmun)
  - Return STRICT JSON ONLY.

JSON structure:
{
  "persons": [
    {
      "name_native": "",
      "name_latin": "",
      "aliases": [],
      "current_position": "",
      "service_or_agency": "",
      "rank_or_grade": "",
      "thematic_keywords": []
    }
  ],
  "organizations": [
    {
      "name": "",
      "type": "",
      "parent_org": ""
    }
  ]
}

Text:
{{TEXT}}
"""

    relationship_prompt_template: str = """
Extract all relationships between persons and organizations in Korean-language
text about the DPRK (North Korea).

Focus on:
  - appointments and dismissals
  - promotions and demotions
  - command relationships
  - party-state-military linkages
  - participation in meetings, inspections, and guidance visits

Return STRICT JSON ONLY:
{
  "edges": [
    {
      "source": "",
      "target": "",
      "relationship_type": "",
      "weight": 1.0
    }
  ]
}

Text:
{{TEXT}}
"""

    event_prompt_template: str = """
Extract political, military, and security-related events from Korean-language
text about the DPRK (North Korea).

Event types include:
  - appointments and dismissals
  - reshuffles and reorganizations
  - military promotions and demotions
  - inspections, guidance visits, and on-the-spot field guidance
  - major meetings (party congresses, plenums, SAC meetings)
  - parades, tests, and exercises

Return STRICT JSON ONLY:
{
  "events": [
    {
      "type": "",
      "persons": [],
      "organizations": [],
      "date": "",
      "description": ""
    }
  ]
}

Text:
{{TEXT}}
"""
