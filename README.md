# Key Person Vulnerability Simulator (KPVS) v1.0.0

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![MTS Research](https://img.shields.io/badge/MTS-Working%20Paper%205-darkblue)](https://ssrn.com/author=10825096)

Monte Carlo simulation tool for quantifying **Key Person Vulnerability (KPV)**
in organizational networks. Identifies which roles represent national security
single points of failure, simulates adversarial targeting scenarios, and
optimises succession-depth investment.

**Companion tool to:**
- [Cost-Asymmetry Simulator (CAS)](https://github.com/rjgreenresearch/cost-asymmetry-simulator) — defence procurement depletion analysis
- MTS Research Programme — [ssrn.com/author=10825096](https://ssrn.com/author=10825096)

---

## The Problem

Standard workforce analysis treats human capital as a **pipeline problem**:
are there enough workers of the required type? The more dangerous vulnerability
is **concentration**: critical national capability residing in a specific,
identifiable, non-substitutable individual whose loss produces a capability
gap no pipeline investment can quickly close.

KPVS quantifies this through the **Key Person Concentration Index (KPCI)**
and three Monte Carlo scenarios that demonstrate the *adversarial targeting gap* —
the additional capability degradation a sophisticated adversary achieves by
targeting high-KPCI roles versus random attrition.

---

## Quick Start

```bash
git clone https://github.com/rjgreenresearch/kpv-simulator.git
cd kpv-simulator
python main.py --demo
```

No external dependencies. Requires Python ≥ 3.10.

---

## The KPCI Framework

**KPCI = ST + DR + AO** (each component [0, 4]; composite [0, 12])

| Component | Name | What It Measures |
|-----------|------|-----------------|
| **ST** | Substitution Timeline | Time to restore 80% effectiveness under optimal succession |
| **DR** | Documentation Ratio | Fraction of role value that is tacit / undocumented |
| **AO** | Adversarial Observability | External identifiability as a high-value target |

**Tier classification:**

| KPCI | Tier | Action |
|------|------|--------|
| 10–12 | Tier-1 KPV | **URGENT** — ≥2 successors in active development |
| 7–9 | Tier-2 KPV | **HIGH** — formalise succession plan immediately |
| 4–6 | Manageable | Standard succession planning adequate |
| 0–3 | Resilient | Institutional processes provide resilience |

---

## Three Simulation Scenarios

### 1. Random Attrition (Baseline)
Removes N roles uniformly at random — models natural turnover.
Provides the null-hypothesis distribution.

### 2. Adversarial Targeting
Removes N roles preferentially targeting highest-KPCI nodes
(accuracy configurable; default 85%). Models Thousand Talents-style
systematic identification and exploitation of irreplaceable nodes.

**Key output:** Adversarial Gap (percentage points below random attrition)
— the exploitation premium a sophisticated adversary achieves.

### 3. Cascade Failure
Stochastic propagation from loss of one mission-critical role to
its dependent network. Estimates mean residual capability and
restoration timeline.

---

## Bench Investment Optimizer

Greedy marginal-improvement algorithm determines the **optimal allocation
of succession-depth investments** across roles — analogous to the CAS
simulator's optimal $1B portfolio allocation for weapons procurement.

```
python main.py --example rare_earth --budget 5
```

---

## Built-in Example Organisations

| Example | Sector | Key Finding |
|---------|--------|-------------|
| `rare_earth` | REE Processing | Chief Separation Chemist: KPCI 11.0, 72-month restoration, 0 bench |
| `nuclear` | Stockpile Stewardship | Senior Warhead Designer: KPCI 12.0 — maximum vulnerability |
| `pharma` | KSM Synthesis | Chief Process Chemist: KPCI 10.0, active Thousand Talents target profile |

---

## Canonical Run

The canonical run for Paper 5 citation:

```bash
python main.py --example rare_earth \
               --iterations 10000    \
               --seed 20260501       \
               --budget 3            \
               --json-dir runs/
```

Cite as: `KPVS v1.0.0, seed=20260501, N=10,000`

---

## CLI Reference

```
python main.py --demo                          # all three examples
python main.py --example rare_earth            # single example
python main.py --org my_org.json               # custom organisation
python main.py --demo --json-dir runs/         # save JSON artefacts
python main.py --demo --quiet --json-dir runs/ # JSON only, no console
python main.py --demo --log-level DEBUG        # verbose logging
```

Full CLI reference: [docs/user_guide.md](docs/user_guide.md)

---

## Test Suite

```bash
pip install pytest pytest-cov
pytest                                    # all tests
pytest --cov=kpvs --cov-report=term-missing
pytest tests/test_simulator.py -v        # single module
pytest -k "adversarial" -v               # keyword filter
```

80+ tests across models, scenarios, optimizer, reporting, and logging.
All tests are deterministic (fixed seeds).

---

## Project Structure

```
kpv-simulator/
├── main.py            CLI entry point
├── kpvs/
│   ├── models.py      Role, Organization, KPCI scoring
│   ├── simulator.py   Three Monte Carlo scenarios
│   ├── optimizer.py   Bench investment optimizer
│   ├── reporting.py   Console + JSON reporters
│   ├── logging_config.py  Centralised logging
│   └── examples.py    Three built-in demo orgs
├── examples/          JSON org files
├── tests/             80+ pytest tests
└── docs/              Architecture, methodology, data sources
```

See [docs/architecture.md](docs/architecture.md) for full design documentation.

---

## Citation

```bibtex
@software{green2026kpvs,
  author  = {Green, Robert J.},
  title   = {{Key Person Vulnerability Simulator (KPVS)}},
  year    = {2026},
  version = {1.0.0},
  url     = {https://github.com/rjgreenresearch/kpv-simulator}
}
```

**Associated paper:**
> Green, R.J. (2026). "The Irreplaceable Node: Key Person Concentration as a
> Compound National Security Vulnerability." MTS Working Paper 5.
> Available: ssrn.com/author=10825096

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

**Author:** Robert J. Green | robert@rjgreenresearch.org |
[rjgreenresearch.org](https://rjgreenresearch.org) |
ORCID: [0009-0002-9097-1021](https://orcid.org/0009-0002-9097-1021)
