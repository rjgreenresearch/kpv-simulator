from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class CountryLLMProfile:
    """
    Base class describing country-specific linguistic, political, and structural
    patterns that guide LLM extraction.

    Subclasses override:
      - naming conventions
      - rank systems
      - political hierarchy
      - common titles
      - language/encoding hints
      - extraction heuristics
    """

    country_code: str

    # ------------------------------------------------------------------
    # Language + Encoding
    # ------------------------------------------------------------------
    language: str = "en"
    encoding: str = "utf-8"

    # ------------------------------------------------------------------
    # Naming conventions
    # ------------------------------------------------------------------
    name_order: str = "western"  # "western" or "eastern"
    surname_first: bool = False
    common_surnames: List[str] = field(default_factory=list)
    honorifics: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Titles, ranks, and political structures
    # ------------------------------------------------------------------
    common_titles: List[str] = field(default_factory=list)
    rank_patterns: List[str] = field(default_factory=list)
    political_hierarchy: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Organizational patterns
    # ------------------------------------------------------------------
    org_keywords: List[str] = field(default_factory=list)
    ministry_keywords: List[str] = field(default_factory=list)
    military_keywords: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Relationship patterns
    # ------------------------------------------------------------------
    appointment_verbs: List[str] = field(default_factory=lambda: [
        "appointed", "named", "designated", "promoted", "assigned"
    ])
    meeting_verbs: List[str] = field(default_factory=lambda: [
        "met with", "held talks with", "conferred with"
    ])
    inspection_verbs: List[str] = field(default_factory=lambda: [
        "inspected", "visited", "reviewed"
    ])

    # ------------------------------------------------------------------
    # Risk + Security posture
    # ------------------------------------------------------------------
    bot_risk: str = "medium"  # low / medium / high
    requires_proxy: bool = False
    requires_session: bool = False
    blocks_us_ips: bool = False

    # ------------------------------------------------------------------
    # Prompt tuning parameters
    # ------------------------------------------------------------------
    max_entities: int = 50
    max_edges: int = 100
    max_events: int = 50

    # ------------------------------------------------------------------
    # Prompt templates (subclasses override)
    # ------------------------------------------------------------------
    entity_prompt_template: str = """
Extract all persons and organizations from the following text.

Return STRICT JSON with this structure:
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
Extract all relationships between persons and organizations.

Return STRICT JSON with this structure:
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
Extract all political or military events (promotions, purges, reshuffles, inspections).

Return STRICT JSON with this structure:
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

    # ------------------------------------------------------------------
    # Utility: render prompt
    # ------------------------------------------------------------------
    def render_prompt(self, template: str, text: str) -> str:
        """
        Simple template renderer. Subclasses may override for more complex logic.
        """
        return template.replace("{{TEXT}}", text)
