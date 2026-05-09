# KPVS Person-Centric Layer — Complete Pack (v6)

Final release. Complete person-centric extension of KPVS without modifying
any of the 2.0 codebase. All planned PRs delivered.

## Status

- ✅ PR #1 — Person, Effective KPCI, PRC taxonomy
- ✅ PR #1.5 — Structured Alias dataclass + name matching utilities
- ✅ PR #2 — Person-aware adversarial targeting
- ✅ PR #3 — Graph-aware cascade propagation
- ✅ PR #4 — Faction purge scenario
- ✅ PR #5 — Entity resolver with calibration

**Test count: 149/149 passing across 6 test files.**

## Architecture summary

```
                      ┌─────────────────────────┐
                      │    KPVSimulator (2.0)    │  unchanged
                      └─────────────┬───────────┘
                                    ↓ (inherits)
                      ┌─────────────────────────┐
                      │   PersonAwareSimulator   │  PR #2
                      │  • random attrition      │
                      │  • adversarial targeting │
                      └─────────────┬───────────┘
                                    ↓
                      ┌─────────────────────────┐
                      │  FactionAwareSimulator   │  PR #4
                      │  • faction purge         │
                      └─────────────┬───────────┘
                                    ↓
                      ┌─────────────────────────┐
                      │   GraphAwareSimulator    │  PR #3
                      │  • graph cascade         │
                      └─────────────────────────┘

  Data layer:                  Cross-cutting:
  ─────────────                ────────────────
  Person (PR #1)               EntityResolver (PR #5)
  Alias (PR #1.5)              name_matching (PR #1.5)
  RoleAssignment (PR #1)       OSINTGraph (PR #3)
  factions tag (PR #4)
```

Use `GraphAwareSimulator` as the drop-in replacement for everything —
it inherits all prior scenarios.

## Public API (kpvs/__init__.py)

```python
from kpvs import (
    # Data model
    Person, Alias, RoleAssignment,
    roles_held_by, persons_in_role, multi_hat_persons,

    # Effective KPCI
    effective_kpci, effective_tier, person_premium,
    tenure_factor, continuity_loss,

    # Name matching
    normalize, match_score, find_person, find_persons_above,
    transliteration_variants,

    # Simulators
    PersonAwareSimulator, PersonScenarioResult, person_adversarial_gap,
    FactionAwareSimulator, FactionPurgeResult,
        resolve_faction_members, faction_concentration_premium,
        run_faction_vs_random,
    GraphAwareSimulator, CascadeResult, cascade_vs_seed_only,

    # Graph
    OSINTGraph, GraphEdge, empty_graph, auto_apex_edges,

    # Entity resolver
    EntityResolver, ResolveResult, MergeCandidate, CalibrationReport,
)
```

## Files in this pack

```
kpvs/
├── __init__.py                          # Public API exports         (PR #5)
├── persons.py                           # Person + Alias + Assignment
├── effective_kpci.py                    # Derivation + diagnostics
├── name_matching.py                     # Cross-script fuzzy matching
├── person_simulator.py                  # PersonAwareSimulator
├── faction_purge.py                     # FactionAwareSimulator
├── osint_graph.py                       # OSINTGraph + auto_apex_edges
├── cascade_simulator.py                 # GraphAwareSimulator
├── entity_resolver.py                   # EntityResolver               (PR #5)
└── intelligence/
    └── role_mapper.py                   # PRC taxonomy + graph→profile

tests/                       (149 tests total)
├── test_persons.py                      # 24 tests
├── test_person_simulator.py             # 12 tests
├── test_name_matching.py                # 35 tests
├── test_faction_purge.py                # 23 tests
├── test_cascade.py                      # 27 tests
├── test_entity_resolver.py              # 27 tests                    (PR #5)
└── test_integration.py                  # 1 end-to-end smoke test     (PR #5)

examples/
├── prc_person_centric_demo.py           # Effective KPCI walkthrough
├── prc_adversarial_gap_demo.py          # Person-level adversarial gap
├── name_matching_demo.py                # Cross-script fuzzy resolution
├── faction_purge_demo.py                # Wagner-Surovikin synthetic case
├── cascade_demo.py                      # PRC graph cascade synthetic
└── entity_resolver_demo.py              # Bulk OSINT dedup workflow   (PR #5)
```

## What PR #5 delivers

### Single-query resolution with role context

```python
from kpvs import EntityResolver

resolver = EntityResolver(
    population=canonical_persons,        # dict[id, Person]
    role_assignments=assignments,         # for role-context disambiguation
    roles=role_taxonomy,                  # for role title/institution lookup
    graph=osint_graph,                    # optional — graph-evidence boost
    threshold=0.85,
)

# Three flavors of role context (any combination)
result = resolver.resolve(
    "Wang",                               # ambiguous name
    role_hint="Foreign Affairs",         # free-text → token containment
    role_id="CN-PB-FOREIGN",             # exact role ID (highest precision)
    institution="CCP Central Foreign Affairs Commission",
)
# → Wang Yi, score boosted via role context match
```

### Bulk merge candidate generation

```python
candidates = resolver.find_merge_candidates(
    incoming_persons,                     # list[Person] from scrapers
    threshold=0.85,
    include_role_context=True,
)
# → list[MergeCandidate(incoming_id, canonical_id, score, evidence)]
```

### Bulk graph deduplication

```python
deduped_graph = resolver.deduplicate_graph(
    osint_graph,
    candidates,                           # approved merges (after analyst review)
    merge_source="entity-resolver",
)
# - Person nodes consolidated to canonical IDs
# - Edges rewritten + deduplicated
# - Self-loops from rewrites removed
# - person_to_orgs and role_to_org updated
# - Surface strings preserved as Aliases on canonical Person
```

### Calibration against ground truth

```python
report = resolver.calibrate(
    ground_truth=[
        ("Xi Jinping", "P-CN-XI"),
        ("习近平", "P-CN-XI"),
        ("Hsi Chinping", "P-CN-XI"),     # Wade-Giles
        ("Си Цзиньпин", "P-CN-XI"),       # Russian source
        ("John Smith", None),             # should NOT match
        # ...
    ],
    thresholds=[0.50, 0.55, ..., 1.00],
)
# → CalibrationReport(threshold_table, best_f1_threshold, best_f1)
```

Demo output (13 ground-truth pairs against PRC + RU canonical population):

```
 Thresh  Precision    Recall      F1   TP/FP/FN/TN
────────────────────────────────────────────────────
   0.50      1.000     0.909   0.952   10/0/1/2     ← best F1
   0.85      1.000     0.727   0.842    8/0/3/2     ← shipped default
   1.00      1.000     0.545   0.706    6/0/5/2     ← exact-match only
```

Perfect precision across all thresholds (no false positives in this set);
recall drops as fuzzy variants like "Hsi Chinping" and "Си Цзиньпин"
fall below threshold. For adversarial intel work, the 0.85 default's
trade-off (perfect precision, ~73% recall) is appropriate — false
merges contaminate downstream analytics far more than missed merges.

## Dangling items addressed in this pack

1. **`kpvs/__init__.py` clean exports** — was empty; now provides the
   complete public API surface. Downstream code can `from kpvs import …`.

2. **`auto_apex_edges()` helper** — the cascade demo flagged that
   membership alone doesn't trigger Person→Org cascade. Helper auto-
   generates `apex_loss` edges for any person whose effective KPCI
   meets a threshold (default Tier-1, ≥10). Reduces boilerplate when
   building real OSINT graphs.

3. **Integration smoke test** — `tests/test_integration.py` exercises
   the full chain: Person → Effective KPCI → Aliases → Person
   simulator → Faction simulator → Graph cascade → Entity resolver.
   Verifies all six modules compose correctly via the unified imports.

## Run

```bash
python -m pytest tests/ -v                       # 149 tests, ~1s
python examples/entity_resolver_demo.py          # PR #5 workflow demo
```

## Architectural commitments preserved across all PRs

1. **Existing simulator.py is unchanged.** All new scenarios live in
   the inheritance chain rooted at PersonAwareSimulator.
2. **Role-level KPCI methodology unchanged.** ST + DR + AO and tier
   thresholds (10 / 7 / 4) remain the published doctrine. Effective
   KPCI is derived, never stored. Floor invariant guarantees
   `effective ≥ structural`.
3. **Backward compatible at every layer.**
   - `aliases=["foo"]` and `aliases=[Alias(...)]` and
     `aliases=[{"text": "foo"}]` all work.
   - GraphAwareSimulator can be constructed without a graph.
   - EntityResolver works with just population (no roles, no graph).
4. **NetworkX is optional.** Used opportunistically for graph metrics;
   degree-only fallback when not available.
5. **Reproducibility.** Every Monte Carlo scenario accepts a seed.
   Tests verify identical seeds produce identical output.

## What's NOT in this pack (intentional out-of-scope)

- ML-based name matching (transformer embeddings, BERT-NER)
- External knowledge-base lookups (Wikipedia, Wikidata)
- Active learning loops for resolver
- Cross-graph merging across multiple OSINTGraph instances
- Visualization (recommend external tools — Gephi, Cytoscape)
- Time-series analysis (snapshots over multiple dates)

These are appropriate v2 features when there's empirical demand and
calibration data to inform their design.

## Calibration suggestions for production use

Real-world thresholds and edge weights need calibration against your
specific OSINT pipeline. Sensible historical-event ground-truth datasets:

| Event                                  | Tests                              |
|----------------------------------------|------------------------------------|
| Bo Xilai 2012 → Zhou Yongkang isolation| CCP `factional` + `patron` edges  |
| Soleimani Jan 2020 → IRGC-QF cohort   | `reports_to` + `mentor`            |
| Wagner-Surovikin June 2023            | `patron` + `co_event`              |
| Jang Song-thaek Dec 2013 (DPRK)       | `family` + `reports_to`            |
| Hu Jintao Oct 2022 PB removal         | Single-decap continuity loss      |

A calibration paper using these events would let your published
methodology defend its concentration premium and cascade premium
numbers as empirically grounded rather than purely heuristic.

## Version

`__version__ = "0.5.0"` — corresponds to PRs #1 + #1.5 + #2 + #3 + #4 + #5.
