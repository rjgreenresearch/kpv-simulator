# User Guide — KPVS v1.0.0

## Installation

```bash
# Clone the repository
git clone https://github.com/rjgreenresearch/kpv-simulator.git
cd kpv-simulator

# (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install (no external runtime dependencies required)
pip install -e .
```

## Quick Start

```bash
# Run all three built-in example organisations
python main.py --demo

# Run a single example with 10,000 iterations
python main.py --example rare_earth --iterations 10000

# Analyse a custom organisation
python main.py --org examples/rare_earth_org.json

# Save JSON artefacts to a run directory
python main.py --demo --json-dir runs/

# Suppress console; write JSON only
python main.py --demo --quiet --json-dir runs/
```

## Custom Organisation JSON

Create a JSON file following the schema in `examples/rare_earth_org.json`:

```json
{
  "name": "My Organisation",
  "description": "Optional description.",
  "mission_critical_roles": ["cto", "chief_scientist"],
  "roles": [
    {
      "id": "cto",
      "title": "Chief Technology Officer",
      "substitution_timeline": 3.0,
      "documentation_ratio": 2.5,
      "adversarial_observability": 4.0,
      "reports_to": "ceo",
      "critical_dependencies": ["chief_scientist"],
      "capability_weight": 3.0,
      "bench_depth": 0,
      "notes": "Optional free-text annotation."
    }
  ]
}
```

### KPCI Component Scoring Guide

| Component | 0 | 1 | 2 | 3 | 4 |
|-----------|---|---|---|---|---|
| **ST** (Substitution Timeline) | <3 months | 3–6 months | 6–18 months | 18–36 months | 36+ months |
| **DR** (Documentation Ratio — tacit fraction) | <10% tacit | 10–30% | 30–60% | 60–90% | >90% tacit |
| **AO** (Adversarial Observability) | Anonymous | Low profile | Moderate | High | Publicly documented critical role |

## CLI Reference

```
python main.py [OPTIONS]

Source (mutually exclusive):
  --demo              Run all three built-in examples
  --example NAME      Run one example: rare_earth | nuclear | pharma
  --org FILE          Load a custom organisation JSON

Simulation:
  -N, --iterations N  Monte Carlo iterations (default: 10,000)
  --seed SEED         RNG seed (default: 20260501)
  --n-losses K        Roles lost per iteration (default: 20% of org)
  --targeting-accuracy P  Adversarial accuracy in (0,1] (default: 0.85)
  --budget B          Bench investment units for optimizer (default: 3)
  --skip-cascade      Skip cascade failure scenarios
  --skip-optimizer    Skip bench investment optimizer

Output:
  --json-dir DIR      Write JSON artefacts to DIR
  -q, --quiet         Suppress console output

Logging:
  --log-level LEVEL   DEBUG | INFO | WARNING | ERROR (default: INFO)
  --log-file FILE     Log file path (auto-generated if omitted)
  --no-log-file       Disable file logging
```

## Python API

```python
from kpvs import Organization, KPVSimulator, BenchOptimizer
from kpvs.examples import build_rare_earth_org

# Load a built-in example
org = build_rare_earth_org()

# Run simulation
sim = KPVSimulator(org, seed=20260501)
random_result    = sim.scenario_random_attrition(n_losses=2, n_iterations=10_000)
adversarial_result = sim.scenario_adversarial_targeting(n_losses=2, n_iterations=10_000)
cascade_result   = sim.scenario_cascade_failure("chief_sep_chemist", n_iterations=10_000)

print(f"Adversarial gap: {random_result.mean_pct - adversarial_result.mean_pct:.1f} pp")

# Optimise bench investment
optimizer = BenchOptimizer(org, seed=20260501)
opt = optimizer.optimise(budget_units=3)
print(f"Improvement: +{opt.improvement_pp:.1f} pp")

# Load from JSON
import json
with open("examples/rare_earth_org.json") as f:
    org = Organization.from_dict(json.load(f))
```

## Running the Test Suite

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests (verbose)
pytest

# Run with coverage report
pytest --cov=kpvs --cov-report=term-missing

# Run a specific test file
pytest tests/test_models.py -v

# Run tests matching a keyword
pytest -k "adversarial" -v
```

## Reproducibility

All results are fully reproducible via the seed parameter:

```bash
python main.py --example rare_earth --seed 20260501 --iterations 10000
```

Cite canonical runs as:
`KPVS v1.0.0, run_YYYYMMDD_HHMMSS, seed=20260501, N=10000`

The run_id and all parameters are embedded in every JSON output file.

## Citation

```bibtex
@software{green2026kpvs,
  author    = {Green, Robert J.},
  title     = {{Key Person Vulnerability Simulator (KPVS)}},
  year      = {2026},
  version   = {1.0.0},
  url       = {https://github.com/rjgreenresearch/kpv-simulator},
  license   = {Apache-2.0}
}
```

See also: CITATION.cff for CFF format.
