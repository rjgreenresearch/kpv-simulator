"""
examples/name_matching_demo.py — Cross-script fuzzy person resolution
======================================================================

Demonstrates how aliases enable name matching across multi-script OSINT
sources. Builds a small population of PRC + Russian + Iranian leaders
with realistic alias coverage, then runs queries in different scripts
and romanization schemes against them.

This is the foundation the entity resolver in PR #5 will build on.
"""

from kpvs.persons import Person, Alias
from kpvs.name_matching import find_person, find_persons_above


def banner(text: str) -> None:
    print("\n" + "═" * 76)
    print(f"  {text}")
    print("═" * 76)


def build_population() -> dict:
    """Realistic alias coverage for a small leadership population."""
    return {
        "P-CN-XI": Person(
            id="P-CN-XI",
            name="Xi Jinping",
            country="CN",
            name_native="习近平",
            tacit_knowledge=4.0, network_integration=4.0,
            tenure_months=156, substitutes=0,
            aliases=[
                Alias(text="Hsi Chin-p'ing", language="zh",
                      romanization="wade-giles",
                      source="historical-archive"),
                Alias(text="Си Цзиньпин", script="cyrl", language="ru",
                      source="TASS-2024-03-15"),
                Alias(text="シー・チンピン", script="kana", language="ja",
                      source="Asahi-2024-04-22", confidence=0.9),
                Alias(text="시진핑", script="hang", language="ko",
                      source="Yonhap-2024-05-01"),
            ],
        ),
        "P-CN-LI-Q": Person(
            id="P-CN-LI-Q",
            name="Li Qiang",
            country="CN",
            name_native="李强",
            aliases=[
                Alias(text="Li Ch'iang", romanization="wade-giles"),
                Alias(text="Ли Цян", script="cyrl", language="ru"),
            ],
        ),
        "P-CN-WANG-H": Person(
            id="P-CN-WANG-H",
            name="Wang Huning",
            country="CN",
            name_native="王沪宁",
            aliases=[Alias(text="Wang Hu-ning", romanization="wade-giles")],
        ),
        "P-CN-WANG-Y": Person(
            id="P-CN-WANG-Y",
            name="Wang Yi",
            country="CN",
            name_native="王毅",
            aliases=[Alias(text="Wang I", romanization="wade-giles")],
        ),
        "P-RU-PUTIN": Person(
            id="P-RU-PUTIN",
            name="Vladimir Putin",
            country="RU",
            name_native="Владимир Путин",
            aliases=[
                Alias(text="V.V. Putin", source="generic-news"),
                Alias(text="Vladimir Vladimirovich Putin",
                      notes="full patronymic form"),
                Alias(text="В.В. Путин", script="cyrl", language="ru"),
            ],
        ),
        "P-RU-LAVROV": Person(
            id="P-RU-LAVROV",
            name="Sergey Lavrov",
            country="RU",
            name_native="Сергей Лавров",
            aliases=[
                Alias(text="Sergei Lavrov",
                      notes="alternate Anglo romanization"),
                Alias(text="С.В. Лавров", script="cyrl", language="ru"),
            ],
        ),
        "P-IR-KHAMENEI": Person(
            id="P-IR-KHAMENEI",
            name="Ali Khamenei",
            country="IR",
            name_native="علی خامنه‌ای",
            aliases=[
                Alias(text="Sayyid Ali Hosseini Khamenei",
                      notes="full honorific form"),
                Alias(text="Khāmenei", confidence=0.95,
                      notes="diacritic-marked transliteration"),
                Alias(text="Али Хаменеи", script="cyrl", language="ru"),
            ],
        ),
        "P-KP-KIM": Person(
            id="P-KP-KIM",
            name="Kim Jong Un",
            country="KP",
            name_native="김정은",
            aliases=[
                Alias(text="Kim Jong-un", romanization="revised"),
                Alias(text="Kim Chong Un", romanization="mccune-reischauer"),
                Alias(text="金正恩", script="hani", language="zh",
                      source="Xinhua-2024"),
                Alias(text="Ким Чен Ын", script="cyrl", language="ru"),
            ],
        ),
    }


def query(population: dict, q: str, threshold: float = 0.85) -> None:
    """Run a query, print result."""
    result = find_person(q, population, threshold=threshold)
    if result is None:
        print(f"  ✗ '{q}'  → no match (threshold {threshold:.2f})")
        return
    person, score, matched = result
    print(f"  ✓ '{q}'")
    print(f"     → {person.name} ({person.id})  score={score:.3f}")
    print(f"     matched alias: '{matched}'")


def main() -> None:
    population = build_population()

    banner("CROSS-SCRIPT FUZZY MATCHING ON 8 LEADERS")
    print(f"\n  Population: {len(population)} persons")
    print(f"  Total aliases: {sum(len(p.aliases) for p in population.values())}")
    print(f"  Scripts covered: latin, hans, cyrl, arab, hang, kana, hani")

    # ── 1. Native script queries ─────────────────────────────────────────
    banner("1. NATIVE-SCRIPT QUERIES (highest confidence)")
    print()
    query(population, "习近平")          # Chinese characters
    query(population, "Владимир Путин")  # Russian Cyrillic
    query(population, "علی خامنه‌ای")     # Persian Arabic script
    query(population, "김정은")          # Korean Hangul

    # ── 2. Wade-Giles (older Anglosphere transliteration) ────────────────
    banner("2. WADE-GILES QUERIES (legacy English-language sources)")
    print()
    query(population, "Hsi Chin-p'ing")
    query(population, "Hsi Chinping")
    query(population, "Wang Hu-ning")
    query(population, "Kim Chong Un")

    # ── 3. Russian-source spellings ──────────────────────────────────────
    banner("3. RUSSIAN-SOURCE SPELLINGS (TASS / RIA Novosti style)")
    print()
    query(population, "Си Цзиньпин")     # Russian rendering of Chinese name
    query(population, "Ли Цян")
    query(population, "Али Хаменеи")
    query(population, "Ким Чен Ын")

    # ── 4. Casual / abbreviated forms ────────────────────────────────────
    banner("4. ABBREVIATED & VARIANT FORMS")
    print()
    query(population, "V.V. Putin")
    query(population, "Vladimir Vladimirovich Putin")
    query(population, "Sergei Lavrov")   # vs Sergey Lavrov (canonical)
    query(population, "Khāmenei")        # diacritic variant
    query(population, "Sayyid Ali Hosseini Khamenei")  # full honorific

    # ── 5. Reversed name order ───────────────────────────────────────────
    banner("5. NAME-ORDER VARIANTS")
    print()
    query(population, "Jinping Xi", threshold=0.85)   # Western order
    query(population, "Putin, Vladimir")              # Last, First

    # ── 6. Ambiguous queries (find all above threshold) ──────────────────
    banner("6. AMBIGUOUS QUERIES — surface all candidates")
    print()
    print("  Query: 'Wang' (matches multiple Politburo members)")
    matches = find_persons_above("Wang", population, threshold=0.4)
    for person, score, text in matches:
        print(f"    {score:.3f}  {person.name:<22} (matched '{text}')")

    print()
    print("  Query: 'Xi' (high false-positive risk for short queries)")
    matches = find_persons_above("Xi", population, threshold=0.4)
    for person, score, text in matches:
        print(f"    {score:.3f}  {person.name:<22} (matched '{text}')")

    # ── 7. Failure modes ─────────────────────────────────────────────────
    banner("7. FAILURE MODES (queries that should NOT match)")
    print()
    query(population, "Jiang Zemin")   # not in population
    query(population, "John Smith")    # unrelated entirely
    query(population, "Xi")             # too generic at threshold 0.85

    banner("INTERPRETATION")
    print("""
  This module is the FOUNDATION for entity resolution, not the resolver
  itself. Successes shown:
    ✓ Native-script direct match (1.000 score)
    ✓ Wade-Giles ↔ Pinyin translation (0.85+)
    ✓ Cyrillic-source variants (matched via aliases)
    ✓ Reversed name order (token-set match)
    ✓ Honorific & patronymic forms (when included as aliases)

  Limitations the resolver in PR #5 will address:
    • Auto-discovery of aliases from graph context (not requiring
      pre-curation)
    • Disambiguation when multiple candidates score similarly
      (e.g., resolving 'Wang' to a specific Politburo member based on
       co-occurring role context like 'Foreign Minister Wang')
    • Confidence calibration against ground-truth pairs
    • Bulk graph deduplication
""")


if __name__ == "__main__":
    main()
