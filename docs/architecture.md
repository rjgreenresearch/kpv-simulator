# Architecture — KPVS

## Project Layout

```
kpv-simulator/
├── main.py                  ← CLI entry point (argparse)
├── kpvs/
│   ├── __init__.py          ← Public API; version string
│   ├── models.py            ← Role, Organization data models; KPCI scoring
│   ├── simulator.py         ← KPVSimulator: 3 Monte Carlo scenarios
│   ├── optimizer.py         ← BenchOptimizer: greedy allocation
│   ├── reporting.py         ← ConsoleReporter, JSONReporter
│   ├── logging_config.py    ← Centralised logging setup
│   └── examples.py          ← 3 built-in demo organisations
├── examples/
│   └── rare_earth_org.json  ← JSON schema reference + REE example
├── tests/
│   ├── conftest.py          ← Shared fixtures (minimal_org, etc.)
│   ├── test_models.py       ← Role / Organization unit tests
│   ├── test_simulator.py    ← All 3 scenarios + helpers
│   ├── test_optimizer.py    ← BenchOptimizer unit + integration
│   ├── test_reporting.py    ← JSON/console output tests
│   └── test_logging_config.py ← Logging configuration tests
├── docs/
│   ├── architecture.md      ← This file
│   ├── methodology.md       ← KPCI theory and model equations
│   ├── data_sources.md      ← Source calibration for built-in examples
│   └── user_guide.md        ← Step-by-step usage guide
├── .gitignore
├── CHANGELOG.md
├── CITATION.cff
├── LICENSE                  ← Apache 2.0
├── README.md
├── requirements.txt
└── setup.py
```

## Data Flow

```
User Input (JSON / CLI flags)
        │
        ▼
  Organization.from_dict()          models.py
  ├── Role validation (KPCI scoring)
  └── Graph validation (deps/reports_to)
        │
        ▼
  KPVSimulator                      simulator.py
  ├── scenario_random_attrition()
  │     └── _capability_after_loss()  [N iterations]
  ├── scenario_adversarial_targeting()
  │     └── KPCI-ranked targeting + _capability_after_loss()
  └── scenario_cascade_failure()
        └── Stochastic propagation + _capability_after_loss()
        │
        ▼ SimulationResult (distributional statistics)
        │
        ▼
  BenchOptimizer                    optimizer.py
  └── Greedy marginal-improvement over budget_units
        │
        ▼ OptimizationResult
        │
        ▼
  ConsoleReporter / JSONReporter    reporting.py
  └── Formatted tables + JSON artefacts
```

## Key Design Decisions

### Pure Standard Library
KPVS has zero runtime dependencies beyond Python ≥ 3.10.
This ensures it runs in air-gapped environments common in
national security research settings.

### Deterministic by Default
Every Monte Carlo run is seeded. The canonical seed (20260501)
produces identical output across platforms. Results in Paper 5
reference the specific `run_id` and seed.

### Immutable SimulationResult
`SimulationResult` is a frozen dataclass — distributions are
computed once and stored. This prevents accidental mutation
of results between reporter calls.

### Modular Scenarios
Each scenario is a self-contained method returning a
`SimulationResult`. Adding a fourth scenario (e.g., compound
multi-role targeting) requires only a new method in `simulator.py`
and corresponding tests.

### Greedy Optimizer
The `BenchOptimizer` uses greedy marginal improvement rather than
exhaustive search. For organizations with ≤ 50 roles and ≤ 10
budget units, the greedy approach finds near-optimal solutions
at O(budget × roles × eval_iterations) cost.
