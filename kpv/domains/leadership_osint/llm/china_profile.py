from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .country_profile import CountryLLMProfile


@dataclass
class ChinaLLMProfile(CountryLLMProfile):
    """
    China-specific LLM profile.
    Encodes linguistic, political, and organizational patterns
    that guide Claude extraction for PRC/CCP/PLA content.
    """

    country_code: str = "CN"

    # ------------------------------------------------------------------
    # Language + Encoding
    # ------------------------------------------------------------------
    language: str = "zh"
    encoding: str = "utf-8"

    # ------------------------------------------------------------------
    # Naming conventions
    # ------------------------------------------------------------------
    # Chinese names are surname-first (e.g., 李尚福 → Li Shangfu)
    name_order: str = "eastern"
    surname_first: bool = True

    # Common Chinese surnames (top 100)
    common_surnames: List[str] = field(default_factory=lambda: [
        "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
        "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
        "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧"
    ])

    honorifics: List[str] = field(default_factory=lambda: [
        "同志", "书记", "部长", "主任", "委员", "局长", "司长"
    ])

    # ------------------------------------------------------------------
    # Titles, ranks, and political structures
    # ------------------------------------------------------------------
    common_titles: List[str] = field(default_factory=lambda: [
        "书记", "副书记", "部长", "副部长", "主任", "局长",
        "司长", "政委", "司令员", "院长", "所长"
    ])

    # PLA rank patterns
    rank_patterns: List[str] = field(default_factory=lambda: [
        "上将", "中将", "少将", "大校", "上校", "中校", "少校"
    ])

    # CCP hierarchy (descending)
    political_hierarchy: List[str] = field(default_factory=lambda: [
        "中央政治局常委",
        "中央政治局委员",
        "中央书记处书记",
        "中央委员会委员",
        "中央委员会候补委员",
        "省委书记",
        "省长",
        "市委书记",
        "市长"
    ])

    # ------------------------------------------------------------------
    # Organizational patterns
    # ------------------------------------------------------------------
    org_keywords: List[str] = field(default_factory=lambda: [
        "委员会", "部", "局", "司", "院", "所", "集团", "公司", "大学"
    ])

    ministry_keywords: List[str] = field(default_factory=lambda: [
        "外交部", "国防部", "公安部", "工信部", "财政部", "教育部",
        "科技部", "国家发改委", "国家安全部"
    ])

    military_keywords: List[str] = field(default_factory=lambda: [
        "中央军委", "解放军", "火箭军", "海军", "空军", "陆军",
        "武警", "战略支援部队"
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
    max_entities: int = 100
    max_edges: int = 200
    max_events: int = 100

    # ------------------------------------------------------------------
    # Prompt templates (China-specific overrides)
    # ------------------------------------------------------------------
    entity_prompt_template: str = """
You are extracting structured leadership data from Chinese-language political,
military, and state-media text.

Follow these rules:
  - Chinese names are surname-first.
  - Convert names to both native (Chinese) and Latin (pinyin) forms.
  - Identify PLA ranks, CCP titles, and SOE leadership roles.
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
Extract all relationships between persons and organizations in Chinese political,
military, and state-media text.

Focus on:
  - appointments
  - promotions
  - demotions
  - inspections
  - command relationships
  - affiliations

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
Extract political and military events from Chinese-language text.

Event types include:
  - promotions
  - purges
  - disciplinary actions
  - inspections
  - doctrinal statements
  - reshuffles

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
