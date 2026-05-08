from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .country_profile import CountryLLMProfile


@dataclass
class RussiaLLMProfile(CountryLLMProfile):
    """
    Russia-specific LLM profile.

    Encodes:
      - Russian naming conventions (given + patronymic + surname)
      - Kremlin / Government / Duma / Federation Council hierarchy
      - MOD + security services (FSB, SVR, GRU, Rosgvardia)
      - state media narrative patterns (TASS, RIA, Interfax, RG)
    """

    country_code: str = "RU"

    # ------------------------------------------------------------------
    # Language + Encoding
    # ------------------------------------------------------------------
    language: str = "ru"
    encoding: str = "utf-8"

    # ------------------------------------------------------------------
    # Naming conventions
    # ------------------------------------------------------------------
    # Russian names: given name + patronymic + surname (e.g., Сергей Викторович Лавров)
    name_order: str = "western"
    surname_first: bool = False

    common_surnames: List[str] = field(default_factory=lambda: [
        "Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов",
        "Соколов", "Лебедев", "Козлов", "Новиков", "Морозов", "Егоров",
        "Волков", "Соловьёв", "Борисов", "Фёдоров", "Михайлов", "Андреев"
    ])

    honorifics: List[str] = field(default_factory=lambda: [
        "товарищ", "господин", "госпожа"
    ])

    # ------------------------------------------------------------------
    # Titles, ranks, and political structures
    # ------------------------------------------------------------------
    common_titles: List[str] = field(default_factory=lambda: [
        "Президент", "Премьер-министр", "Министр", "Заместитель министра",
        "Председатель", "Заместитель председателя", "Секретарь",
        "Спикер", "Губернатор", "Полномочный представитель"
    ])

    # MOD / security ranks
    rank_patterns: List[str] = field(default_factory=lambda: [
        "генерал армии", "генерал-полковник", "генерал-лейтенант",
        "генерал-майор", "полковник", "подполковник", "майор"
    ])

    # Political hierarchy (descending)
    political_hierarchy: List[str] = field(default_factory=lambda: [
        "Президент Российской Федерации",
        "Председатель Правительства Российской Федерации",
        "Первый заместитель Председателя Правительства",
        "Заместитель Председателя Правительства",
        "Министр",
        "Губернатор субъекта Федерации",
        "Председатель Государственной Думы",
        "Председатель Совета Федерации"
    ])

    # ------------------------------------------------------------------
    # Organizational patterns
    # ------------------------------------------------------------------
    org_keywords: List[str] = field(default_factory=lambda: [
        "Администрация Президента", "Правительство Российской Федерации",
        "Государственная Дума", "Совет Федерации", "Министерство",
        "Федеральная служба", "Федеральное агентство", "Госкорпорация",
        "ПАО", "АО"
    ])

    ministry_keywords: List[str] = field(default_factory=lambda: [
        "Министерство обороны", "Министерство иностранных дел",
        "Министерство внутренних дел", "Министерство финансов",
        "Министерство юстиции", "Министерство энергетики",
        "Министерство промышленности и торговли"
    ])

    military_keywords: List[str] = field(default_factory=lambda: [
        "Министерство обороны", "Генеральный штаб", "Вооружённые силы",
        "Росгвардия", "ФСБ", "СВР", "ГРУ"
    ])

    # ------------------------------------------------------------------
    # Security posture
    # ------------------------------------------------------------------
    bot_risk: str = "high"
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
    # Prompt templates (Russia-specific overrides)
    # ------------------------------------------------------------------
    entity_prompt_template: str = """
You are extracting structured leadership data from Russian-language political,
military, security, and state-media text.

Follow these rules:
  - Russian names often include given name, patronymic, and surname.
  - Preserve full native (Cyrillic) form and provide Latin transliteration.
  - Identify ranks, titles, and roles in:
      * Kremlin / Presidential Administration
      * Government and ministries
      * State Duma / Federation Council
      * MOD, FSB, SVR, GRU, Rosgvardia
      * State-owned enterprises (Gazprom, Rosneft, Rostec, etc.)
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
Extract all relationships between persons and organizations in Russian political,
military, security, and state-media text.

Focus on:
  - appointments and dismissals
  - promotions and demotions
  - command relationships
  - board memberships and SOE leadership
  - meetings and negotiations
  - affiliations with ministries, services, and corporations

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
Extract political, military, and security-related events from Russian-language text.

Event types include:
  - appointments and dismissals
  - reshuffles and reorganizations
  - sanctions and legal actions
  - military operations and exercises
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
