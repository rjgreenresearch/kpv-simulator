# KPVS Person-Centric Layer — Drop-In Extension Pack (v2)

Adds a person layer + person-centric scenarios to KPVS without modifying
any of the 2.0 codebase. Existing 125+ test suite continues to pass and
existing scenarios continue to produce identical output.

## What's in this v2 pack

```
kpvs/persons.py                          # Person + RoleAssignment dataclasses        (PR #1)
kpvs/effective_kpci.py                   # Effective KPCI derivation                  (PR #1)
kpvs/person_simulator.py                 # PersonAwareSimulator + 2 new scenarios     (PR #2 NEW)
kpvs/intelligence/role_mapper.py         # PRC taxonomy + graph→profile pipeline      (PR #1)
tests/test_persons.py                    # 24 unit tests                              (PR #1)
tests/test_person_simulator.py           # 12 unit tests                              (PR #2 NEW)
examples/prc_person_centric_demo.py      # Effective KPCI walkthrough                 (PR #1)
examples/prc_adversarial_gap_demo.py     # Person-level adversarial gap on PRC org    (PR #2 NEW)
```

**Test count: 36/36 passing.**

## What PR #2 adds

Two new Monte Carlo scenarios that operate at the person level:

```python
sim = PersonAwareSimulator(organization, persons, assignments, seed=42)

# Baseline — remove random PERSONS (each removal cascades to all their roles)
random_result = sim.scenario_person_random_attrition(
    n_iterations=5000, n_persons_per_iter=3)

# Adversarial — rank persons by target_value, target top-K with given accuracy
targeted_result = sim.scenario_person_targeted_attrition(
    n_iterations=5000, n_persons_per_iter=3, accuracy=0.85)

# Person-level adversarial gap
gap = person_adversarial_gap(random_result, targeted_result)
# {'capability_gap_pp': 4.09, 'tacit_shock_premium': 1.56,
#  'roles_disabled_premium': 0.22, 'friction_premium_months': 16.1}
```

### Why a person-level baseline matters

The existing role-level `scenario_random_attrition` removes one role at a
time. Comparing it to person-level adversarial targeting is apples-to-oranges
— it artificially inflates the gap by hiding the multi-hat dynamic on the
baseline side. The new `scenario_person_random_attrition` is the apples-
to-apples comparator: random *persons* dropped, multi-hat cascade preserved
on both sides, and the gap reflects only the adversary's targeting edge.

### Target-value formula

```
target_value(person) = Σ_{r ∈ roles_held(person)} eff_kpci(r, person) × capacity
```

This is the criticality footprint a single targeting operation removes.
Multi-hat persons accumulate target value across their roles, naturally
making them more attractive targets. Capacity weights ensure that a
person holding a 60%-of-attention apex role + 40%-of-attention deputy
role contributes correctly weighted.

## Demo output (5000 iterations, 3 persons/iter, 85% accuracy)

```
Capability gap:                +4.09 pp
  Random:                       81.07% remaining
  Adversarial:                  76.99% remaining
Tacit-shock premium:           +1.56
Roles-disabled premium:        +0.22
Replacement-friction premium:  +16.1 months

Multi-hat efficiency:
  Random:        1.07 roles/person
  Adversarial:   1.14 roles/person
```

The friction premium is the most operationally salient number — a
sophisticated adversary's targeting imposes ~16 additional months of
restoration time per operation by hitting low-substitute persons.

## Where to place files in your existing repo

```
kpv-simulator/
├── kpvs/
│   ├── persons.py                       ← NEW PR #1
│   ├── effective_kpci.py                ← NEW PR #1
│   ├── person_simulator.py              ← NEW PR #2
│   ├── models.py                        (unchanged)
│   ├── simulator.py                     (unchanged — existing scenarios untouched)
│   └── intelligence/
│       ├── role_mapper.py               ← NEW PR #1
│       └── org_loader.py                (unchanged)
├── tests/
│   ├── test_persons.py                  ← NEW PR #1
│   └── test_person_simulator.py         ← NEW PR #2
└── examples/
    ├── prc_person_centric_demo.py       ← NEW PR #1
    └── prc_adversarial_gap_demo.py      ← NEW PR #2
```

## Run

```bash
# Tests (all 36 should pass; existing simulator suite still passes)
python -m pytest tests/ -v

# Effective KPCI walkthrough on PRC org
python examples/prc_person_centric_demo.py

# Person-level adversarial gap
python examples/prc_adversarial_gap_demo.py
```

## Architectural commitments preserved

1. **Existing simulator.py is unchanged.** PersonAwareSimulator wraps an
   existing Organization but does not subclass or modify KPVSimulator.
   You can run both side-by-side.

2. **Role-level KPCI methodology unchanged.** ST + DR + AO and tier
   thresholds (10 / 7 / 4) remain the published doctrine.

3. **Effective KPCI is derived, not stored.** No mutation of Role objects.
   Floor invariant guarantees `effective ≥ structural`.

4. **Backward compatible.** If you don't pass persons/assignments, you
   get exactly the existing KPVSimulator behavior. Existing JSON org
   files in kpvs/intelligence/ continue to load and run unchanged.

## Reproducibility

Both scenarios accept a `seed` argument. Tests verify that identical
seeds produce identical output across runs (test_same_seed_same_results).

## What's NOT in this pack yet (queued)

### PR #3: Graph-aware cascade propagation
Extend `scenario_cascade_failure` to propagate through OSINT graph edges
in addition to existing `critical_dependencies`. Requires the global
graph object on the Organization (or as a separate input).

### PR #4: Faction-purge scenario
New scenario removing a coherent subgraph defined by a faction filter
callable. Highest-value scenario for adversary leadership analysis —
Wagner-affiliated officers, Komi clan, IRGC-QF cohort, Kim family network.

### PR #5: Entity resolver
Cross-source identity stabilization. Xi Jinping / 习近平 / Си Цзиньпин →
single person_id. Fuzzy match + role-context disambiguation against
the curated taxonomies. Should land before role_mapper runs on real
OSINT graph data.

## Tunable coefficients (kpvs/effective_kpci.py)

```python
ALPHA = 0.45                  # weight on tacit knowledge in person premium
BETA = 0.45                   # weight on network integration
GAMMA = 0.60                  # log-substitutes penalty
SUCCESSOR_ST_REDUCTION = 0.5  # designated-successor ST reduction
TENURE_RAMP_MONTHS = 6.0      # learning-curve constant
```

## Calibration suggestions

The 4.1pp gap and +16 month friction premium are sensitive to:

- Coefficient choices (α, β, γ in effective_kpci.py)
- Person profile data quality (TK and CNI from synthetic vs OSINT graph)
- Multi-hat density in the org (more multi-hat → bigger gap)

Sensible follow-on study: calibrate against historical decapitation
events (2022 Hu Jintao removal, 2024 Quds Force commander successions,
the Wagner-Surovikin 2023 dynamics) to validate or tune the coefficients.
