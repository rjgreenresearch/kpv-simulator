# KPVS Person-Centric Layer — Drop-In Extension Pack (v4)

Adds a person layer + person-centric scenarios + structured aliases +
faction-purge scenario to KPVS without modifying any of the 2.0 codebase.

## What's in this v4 pack

```
kpvs/persons.py                          # Person + Alias + RoleAssignment + factions     (PR #1+1.5)
kpvs/effective_kpci.py                   # Effective KPCI derivation                       (PR #1)
kpvs/name_matching.py                    # Cross-script fuzzy matching utilities           (PR #1.5)
kpvs/person_simulator.py                 # PersonAwareSimulator + 2 scenarios              (PR #2)
kpvs/faction_purge.py                    # FactionAwareSimulator + faction-purge scenario  (PR #4 NEW)
kpvs/intelligence/role_mapper.py         # PRC taxonomy + graph→profile pipeline           (PR #1)
tests/test_persons.py                    # Person, Effective KPCI tests                    (PR #1)
tests/test_person_simulator.py           # Simulator scenario tests                        (PR #2)
tests/test_name_matching.py              # Alias, normalization, find_person tests         (PR #1.5)
tests/test_faction_purge.py              # Faction purge tests                             (PR #4 NEW)
examples/prc_person_centric_demo.py      # Effective KPCI walkthrough                      (PR #1)
examples/prc_adversarial_gap_demo.py     # Person-level adversarial gap                    (PR #2)
examples/name_matching_demo.py           # Cross-script fuzzy resolution                   (PR #1.5)
examples/faction_purge_demo.py           # Wagner-Surovikin synthetic case study           (PR #4 NEW)
```

**Test count: 136/136 passing.**

## What PR #4 adds

A new Monte Carlo scenario that operates on coherent leadership subgroups:

```python
from kpvs.faction_purge import FactionAwareSimulator, run_faction_vs_random

sim = FactionAwareSimulator(organization, persons, assignments, seed=42)

# Deterministic: remove ALL members of a tagged faction
result = sim.scenario_faction_purge(faction_tag="wagner-aligned")

# Stochastic: deterministic core + secondary loss probability
result = sim.scenario_faction_purge(
    faction_tag="wagner-aligned",
    secondary_loss_p=0.15,
    n_iterations=3000,
)

# Callable filter for complex membership criteria
result = sim.scenario_faction_purge(
    faction_filter=lambda p: p.tenure_months >= 60 and "GRU" in p.notes,
)

# Compare to equivalent-N random attrition
compare = run_faction_vs_random(sim, faction_tag="wagner-aligned",
                                  n_iterations=2000)
# {'faction': FactionPurgeResult, 'random': PersonScenarioResult,
#  'premium': {'capability_premium_pp': +9.7, ...}}
```

### Faction membership representation

Persons carry a `factions: list[str]` field (added in this PR, backward
compatible — defaults to empty list). A person can hold multiple faction
tags simultaneously:

```python
Person(id="P-RU-005", name="...", country="RU",
       factions=["wagner-aligned", "syria-veteran", "surovikin-line"])
```

Multi-faction persons appear in every relevant purge scenario — natural
modeling of overlapping patronage networks.

### Concentration premium — sign matters

The key output metric is the **concentration premium**: how much worse
a coherent faction purge is than randomly losing the same number of
persons. The sign carries analytical meaning:

| Premium  | Interpretation                                       |
|----------|------------------------------------------------------|
| Positive | Faction concentrated in HIGH-KPCI / high-weight roles. Coherent purge worse than scattered loss. → **Critical single-point-of-failure** |
| ~Zero    | Faction is a representative cross-section of the org. Coherent purge ≈ random equivalent. |
| Negative | Faction holds peripheral roles. Coherent purge LESS damaging than random — random can stochastically hit apex roles the faction doesn't hold. → **Faction is not regime-critical** |

This is operationally meaningful: a positive-premium faction is where
resilience investment pays the highest dividend; a negative-premium
faction is operationally cosmetic to target.

### Demo output (Wagner-Surovikin synthetic case)

```
regime-apex           size= 2  roles= 2  cap=77.3%  premium=  +9.7 pp ← critical
wagner-aligned        size= 6  roles= 7  cap=65.5%  premium=  -5.0 pp
mod-careerist         size= 6  roles= 6  cap=60.2%  premium=  -0.1 pp
syria-veteran         size= 3  roles= 4  cap=80.2%  premium=  -0.0 pp
surovikin-line        size= 2  roles= 3  cap=85.9%  premium=  +0.9 pp
gru-veteran           size= 2  roles= 2  cap=89.8%  premium=  -3.0 pp
```

Matches historical reality: the Wagner-Surovikin June 2023 events
disrupted Russian theater command without threatening regime continuity,
because the regime-apex faction was untouched. The simulator captures
this asymmetry as a sign difference in concentration premium.

### Scenario diagnostics

Beyond mean capability remaining, `FactionPurgeResult` reports:
- `faction_size` and resolved `member_ids`
- `direct_roles_disabled` and `multi_hat_amplification` (extra leverage
  via multi-hat persons inside the faction)
- `direct_tacit_shock` (aggregate TK lost)
- `concentrated_failures` (roles where occupant has ≤1 substitute —
  unreplaceable single-points-of-failure inside the faction)
- `countries_affected` and `cross_org_amplifier` (for transnational
  factions like SCO-bloc, IRGC-Hezbollah, etc.)
- Stochastic spillover: `mean_secondary_loss`, p05/p50/p95 distribution

## Where to place files in your existing repo

```
kpv-simulator/
├── kpvs/
│   ├── persons.py                       (factions field added)
│   ├── faction_purge.py                 ← NEW PR #4
│   ├── name_matching.py                 (unchanged from PR #1.5)
│   ├── effective_kpci.py                (unchanged from PR #1)
│   ├── person_simulator.py              (unchanged from PR #2)
│   ├── models.py                        (unchanged)
│   ├── simulator.py                     (unchanged)
│   └── intelligence/
│       └── role_mapper.py               (unchanged from PR #1)
├── tests/
│   └── test_faction_purge.py            ← NEW PR #4 — 23 tests
└── examples/
    └── faction_purge_demo.py            ← NEW PR #4
```

## Run

```bash
python -m pytest tests/ -v                       # 136 tests
python examples/faction_purge_demo.py            # Wagner case study
```

## Architectural commitments preserved

1. **Existing simulator.py is unchanged.** `FactionAwareSimulator` extends
   `PersonAwareSimulator` via inheritance — drop-in replacement.
2. **Role-level KPCI methodology unchanged.**
3. **Backward compatible.** Existing Person data without `factions` field
   gets empty list default. All prior tests pass.
4. **Inheritance chain.** `FactionAwareSimulator` inherits all
   `PersonAwareSimulator` methods — random attrition, targeted attrition,
   target-value ranking all still work on the new class.

## What's NOT in this pack yet

### PR #3: Graph-aware cascade propagation
Cascade through OSINT graph edges in addition to `critical_dependencies`.
**Still needs your input** on the OSINT graph schema (edge types, per-
country vs unified, person-only vs person+org propagation) before I write code.

### PR #5: Entity resolver
Auto-discover aliases from graph context, calibrate confidence against
ground-truth pairs, bulk graph deduplication. Builds on PR #1.5
infrastructure.

## Tunable parameters

In `kpvs/faction_purge.py`:

```python
# Inside scenario_faction_purge:
secondary_loss_p ∈ [0, 1]   # probability of independent non-faction loss
                            # 0 = deterministic (default)
                            # 0.05–0.20 = realistic post-purge turbulence
                            # >0.30 = regime collapse scenario
n_iterations                # ignored if secondary_loss_p == 0
```

## Calibration suggestion

The Stalin NKVD purges (1936-1938), Saudi 2017 anti-corruption detentions,
Xi's Bo Xilai network purge, and Kim Jong Un's Jang Song-thaek purge all
provide historical concentration-premium data points if reconstructed
from open-source biographical reporting. A future calibration paper
could ground-truth the simulator's concentration premium against these
events.
