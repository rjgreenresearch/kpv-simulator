from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .country_profile import CountryLLMProfile


@dataclass
class IranLLMProfile(CountryLLMProfile):
    """
    Iran-specific LLM profile.

    Encodes:
      - Persian naming conventions (given + father's name + family name)
      - clerical hierarchy (Ayatollah, Hojjatoleslam, etc.)
      - IRGC rank structures
      - ministry + bonyad + SOE patterns
      - security services (IRGC Intelligence, MOIS, LEF)
      - state media narrative patterns (IRNA, Tasnim, Fars)
    """

    country_code: str = "IR"

    # ------------------------------------------------------------------
    # Language + Encoding
    # ------------------------------------------------------------------
    language: str = "fa"
    encoding: str = "utf-8"

    # ------------------------------------------------------------------
    # Naming conventions
    # ------------------------------------------------------------------
    # Persian names: given name + father's name + family name
    name_order: str = "western"
    surname_first: bool = False

    common_surnames: List[str] = field(default_factory=lambda: [
        "محمدی", "حسینی", "رضایی", "احمدی", "جعفری", "کاظمی",
        "موسوی", "نعمتی", "قاسمی", "کریمی", "هاشمی", "شریفی"
    ])

    honorifics: List[str] = field(default_factory=lambda: [
        "حجت‌الاسلام", "آیت‌الله", "سردار", "دکتر", "مهندس"
    ])

    # ------------------------------------------------------------------
    # Titles, ranks, and political structures
    # ------------------------------------------------------------------
    common_titles: List[str] = field(default_factory=lambda: [
        "رئیس‌جمهور", "معاون رئیس‌جمهور", "وزیر", "معاون وزیر",
        "رئیس", "دبیر", "فرمانده", "استاندار"
    ])

    # IRGC rank patterns
    rank_patterns: List[str] = field(default_factory=lambda: [
        "سردار", "سرتیپ", "سرتیپ دوم", "سرلشکر", "سپهبد", "سرهنگ"
    ])

    # Political hierarchy (descending)
    political_hierarchy: List[str] = field(default_factory=lambda: [
        "رهبر جمهوری اسلامی ایران",
        "رئیس‌جمهور",
        "رئیس مجلس شورای اسلامی",
        "رئیس قوه قضائیه",
        "وزیر",
        "استاندار"
    ])

    # ------------------------------------------------------------------
    # Organizational patterns
    # ------------------------------------------------------------------
    org_keywords: List[str] = field(default_factory=lambda: [
        "وزارت", "سازمان", "نهاد", "بنیاد", "سپاه", "ارتش",
        "نیروی انتظامی", "قوه قضائیه", "مجلس", "دولت"
    ])

    ministry_keywords: List[str] = field(default_factory=lambda: [
        "وزارت کشور", "وزارت اطلاعات", "وزارت دفاع",
        "وزارت امور خارجه", "وزارت نفت", "وزارت اقتصاد"
    ])

    military_keywords: List[str] = field(default_factory=lambda: [
        "سپاه پاسداران", "ارتش جمهوری اسلامی", "نیروی قدس",
        "سازمان اطلاعات سپاه", "نیروی انتظامی", "وزارت دفاع"
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
    max_entities: int = 120
    max_edges: int = 250
    max_events: int = 120

    # ------------------------------------------------------------------
    # Prompt templates (Iran-specific)
    # ------------------------------------------------------------------
    entity_prompt_template: str = """
You are extracting structured leadership data from Persian-language political,
military, security, clerical, and state-media text.

Follow these rules:
  - Persian names often include given name + father's name + family name.
  - Preserve full native (Persian) form and provide Latin transliteration.
  - Identify ranks, titles, and roles in:
      * Supreme Leader’s Office
      * Presidency and ministries
      * IRGC, Artesh, LEF
      * MOIS and IRGC Intelligence
      * Bonyads and major SOEs (NIOC, NDFI, MAPNA)
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
Extract all relationships between persons and organizations in Persian political,
military, clerical, and state-media text.

Focus on:
  - appointments and dismissals
  - promotions and demotions
  - command relationships
  - bonyad and SOE leadership
  - IRGC chain of command
  - meetings and negotiations

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
Extract political, military, clerical, and security-related events from Persian text.

Event types include:
  - appointments and dismissals
  - reshuffles and reorganizations
  - sanctions and legal actions
  - IRGC operations and exercises
  - security incidents
  - major SOE leadership changes

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
