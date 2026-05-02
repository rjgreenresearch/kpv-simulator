# Key Person Vulnerability Simulator (KPVS) v1.2.0

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-140%20passing-brightgreen)](tests/)
[![MTS Research](https://img.shields.io/badge/MTS-Working%20Paper%205-darkblue)](https://ssrn.com/author=10825096)

Monte Carlo simulation tool for quantifying **Key Person Vulnerability (KPV)**
in organizational networks. Identifies which roles represent national security
single points of failure, simulates adversarial targeting scenarios, and
optimises succession-depth investment.

Two interfaces: a **command-line tool** for batch analysis and reproducible
citation runs, and a **browser-based web interface** for interactive org editing
and parameter exploration.

**Companion tools:**
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
and three Monte Carlo scenarios that measure the *adversarial targeting gap* —
the additional capability degradation a sophisticated adversary achieves by
selecting high-KPCI targets versus random attrition.

---

## Quick Start

### Command Line

```bash
git clone https://github.com/rjgreenresearch/kpv-simulator.git
cd kpv-simulator
python main.py --demo
```

No runtime dependencies. Requires Python ≥ 3.10.

### Web Interface

```bash
pip install fastapi uvicorn jinja2 python-multipart
python start_webapp.py
```

Opens `http://localhost:8000` automatically. Full org editor, live KPCI
recalculation, Chart.js visualisations, and run history browser.

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

> **AO Inversion for adversarial organizations:** When analysing adversarial
> org structures (China, Russia, Iran, DPRK), AO scores reflect allied
> OSINT visibility rather than adversary visibility. A near-zero adversarial
> targeting gap on these orgs is an *intelligence gap finding*, not a
> resilience finding — it means allied analysts cannot differentiate targets
> because the structure is opaque. Classified AO data would significantly
> widen these gaps.

---

## Four Simulation Scenarios

### 1. Random Attrition (Baseline)
Removes N roles uniformly at random — models natural turnover.
Provides the null-hypothesis distribution against which adversarial
scenarios are tested.

### 2. Adversarial Targeting
Removes N roles preferentially targeting highest-KPCI nodes
(accuracy configurable; default 85%). Models Thousand Talents-style
systematic identification and targeting of irreplaceable nodes.

**Key output:** Adversarial Gap (pp below random attrition) — the
exploitation premium a sophisticated adversary achieves.

### 3. Cascade Failure
Stochastic propagation from loss of one mission-critical role to
its dependent network. Estimates mean residual capability and
restoration timeline per trigger role.

### 4. Bench Investment Optimizer
Greedy marginal-improvement algorithm determines the **optimal allocation
of succession-depth investments** — analogous to the CAS simulator's
optimal $1B portfolio allocation.

```bash
python main.py --example rare_earth --budget 5
```

---

## Built-in Organizations

### Example Sectors (3)

| Key | Sector | Domain | Key Finding |
|-----|--------|--------|-------------|
| `rare_earth` | REE Processing | Material | Chief Sep. Chemist: KPCI 11.0, 72-mo restore, 0 bench |
| `nuclear` | Stockpile Stewardship | Nuclear | Senior Designer: KPCI 12.0 — theoretical maximum |
| `pharma` | KSM Synthesis | Pharmaceutical | Chief Chemist: KPCI 10.0, Thousand Talents target profile |

### Five Eyes National Security (5)

| Key | Nation | Notes |
|-----|--------|-------|
| `us_nsa` | United States | 23 roles · NSA, CIA, CYBERCOM, STRATCOM, DPA Title III |
| `uk` | United Kingdom | GCHQ, MI6, MI5, CPNI key personnel security architecture |
| `ca` | Canada | CSIS, CSE, ICA investment screening |
| `au` | Australia | ASIO, ASD, FIRB · Pine Gap proximity documented |
| `nz` | New Zealand | GCSB, NZSIS · highest Five Eyes adversarial gap |

### Adversarial / PASS Act Designated (4)

| Key | Country | AO Note |
|-----|---------|---------|
| `cn` | People's Republic of China | Near-zero gap on MSS cyber director — intelligence gap |
| `ru` | Russian Federation | Near-zero gap on FSB 18th Centre — intelligence gap |
| `ir` | Islamic Republic of Iran | Nuclear design lead AO=2.0 post-Fakhrizadeh |
| `kp` | DPRK | Most opaque structure; Unit 121 AO=1.0 |

> All data is derived exclusively from publicly available sources.
> No classified materials were consulted. See `docs/intelligence_orgs.md`.

---

## Web Interface

```bash
python start_webapp.py                    # http://localhost:8000
python start_webapp.py --port 8080        # custom port
python start_webapp.py --host 0.0.0.0    # network-accessible
python start_webapp.py --reload           # development auto-reload
```

**Features:**
- **Org selector sidebar** — all 12 organisations by group; custom JSON upload
- **Live org editor** — inline-editable KPCI components, bench depth, and
  capability weight; KPCI recalculates and re-colours in real time as you type
- **Role management** — add roles, delete roles, toggle mission-critical status
- **Parameters panel** — iterations, seed, n-losses, targeting accuracy slider,
  budget, skip cascade / skip optimizer
- **Results panel** — adversarial gap dashboard cards, KPCI bar chart,
  distribution comparison chart, optimizer allocation table, priority
  recommendations, full HTML report embedded in-page
- **Run history** — all past runs listed with org name, gap score, and
  report link; persists across server restarts

**API endpoints** (also accessible via `/docs` for interactive Swagger UI):

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Web UI |
| `GET` | `/api/orgs` | List all organisations with metadata |
| `GET` | `/api/orgs/{key}` | Load a specific org's full JSON |
| `POST` | `/api/run` | Execute simulation; returns results + report URL |
| `GET` | `/api/runs` | Run history |
| `GET` | `/reports/{path}` | Serve generated HTML reports |

---

## HTML Reports

Both the CLI and the web interface produce self-contained HTML reports
that open directly in any browser — no server required.

```bash
# CLI: generate HTML alongside JSON artefacts
python main.py --example rare_earth --iterations 10000 --seed 20260501 \
               --budget 3 --json-dir runs/ --html-dir reports/

# Intelligence orgs with HTML output
python main.py --org-set five_eyes --iterations 10000 --html-dir reports/
python main.py --org-set adversarial --iterations 10000 \
               --skip-optimizer --html-dir reports/
```

**Each run creates a timestamped subdirectory:**
```
reports/
  rare_earth_20260502_075452/
    run_20260502_075452_report.html   ← single-org report
runs/
  rare_earth_20260502_075452/
    run_20260502_075452_summary.json
    run_20260502_075452_kpci_report.json
    ...

reports/
  five_eyes_20260502_081230/
    run_*.html                        ← one per nation
    five_eyes_comparative_report.html ← cross-nation comparison
```

**Report contents:**
- Dashboard cards (adversarial gap, Tier-1 count, zero-bench T1)
- Color-coded KPCI table with inline score bars
- KPCI scores by role (horizontal bar chart)
- Tier distribution (donut chart)
- Capability retention distribution — random vs adversarial (percentile chart)
- Cascade failure cards per mission-critical role
- Bench investment optimizer results
- Priority recommendations

---

## Intelligence Org Analysis

```bash
# List all available org keys
python main.py --list-orgs

# Single intelligence org
python main.py --intel-org cn --iterations 10000 --seed 20260501

# Predefined sets
python main.py --org-set five_eyes    --iterations 10000 --budget 3
python main.py --org-set adversarial  --iterations 10000 --skip-optimizer
python main.py --org-set all_intel    --iterations 10000 --skip-optimizer
python main.py --org-set us_and_china --iterations 10000
```

**Available org sets:** `five_eyes` | `adversarial` | `all_intel` | `us_and_china`

The `--org-set` command produces both individual org reports and a
**comparative HTML report** showing adversarial gaps, Tier-1 counts,
and capability metrics across all organisations side by side.

---

## CLI Reference

```
python main.py [SOURCE] [SIMULATION] [OUTPUT] [LOGGING]

SOURCE (mutually exclusive):
  --demo                    Run all three built-in examples
  --example NAME            rare_earth | nuclear | pharma
  --org FILE                Custom organisation JSON
  --intel-org KEY           us_nsa | uk | ca | au | nz | cn | ru | ir | kp
  --org-set SET             five_eyes | adversarial | all_intel | us_and_china
  --list-orgs               List available org keys and sets, then exit

SIMULATION:
  -N, --iterations N        Monte Carlo iterations (default: 10,000)
  --seed SEED               RNG seed (default: 20260501)
  --n-losses K              Roles lost per iteration (default: 20% of org)
  --targeting-accuracy P    Adversarial accuracy in (0,1] (default: 0.85)
  --budget B                Bench investment units for optimizer (default: 3)
  --skip-cascade            Skip cascade failure scenarios
  --skip-optimizer          Skip bench investment optimizer

OUTPUT:
  --json-dir DIR            JSON artefacts → DIR/<label>_YYYYMMDD_HHMMSS/
  --html-dir DIR            HTML reports  → DIR/<label>_YYYYMMDD_HHMMSS/
  -q, --quiet               Suppress console output

LOGGING:
  --log-level LEVEL         DEBUG | INFO | WARNING | ERROR (default: INFO)
  --log-file FILE           Log file path (auto-generated in logs/ if omitted)
  --no-log-file             Disable file logging
```

---

## Canonical Run (Paper 5 Citation)

```bash
python main.py --example rare_earth \
               --iterations 10000    \
               --seed 20260501       \
               --budget 3            \
               --json-dir runs/      \
               --html-dir reports/
```

Cite as: `KPVS v1.2.0, seed=20260501, N=10,000`

**Key results** (seed=20260502, N=10,000):
- Chief Separation Process Chemist: KPCI 11.0, Tier-1 KPV, 72-month restoration
- Adversarial targeting gap: **17.9 pp** below random attrition (86.7% → 68.7%)
- Optimal 3-unit bench allocation: +2 to Chief Sep. Chemist, +1 to Heavy REE Specialist
- Capability improvement: **68.5% → 91.7%** (+23.2 pp)

---

## Test Suite

```bash
pip install pytest pytest-cov httpx
pytest                                          # all 140 tests
pytest --cov=kpvs --cov-report=term-missing    # with coverage
pytest tests/test_simulator.py -v              # single module
pytest tests/test_reporting_html.py -v         # HTML reporter tests
pytest -k "adversarial" -v                     # keyword filter
```

**140 tests** across: models, simulator (all 3 scenarios), optimizer,
console/JSON reporting, HTML reporting (including web CLI integration),
and logging configuration. All tests are deterministic via fixed seeds.

---

## Project Structure

```
kpv-simulator/
├── main.py                  CLI entry point (argparse)
├── start_webapp.py          Web interface launcher
├── kpvs/
│   ├── __init__.py          Public API; version string
│   ├── models.py            Role, Organization, KPCI scoring
│   ├── simulator.py         Three Monte Carlo scenarios + SimulationResult
│   ├── optimizer.py         BenchOptimizer — greedy allocation
│   ├── reporting.py         ConsoleReporter, JSONReporter
│   ├── reporting_html.py    HTMLReporter — single-org + comparative reports
│   ├── logging_config.py    Centralised logging (rotating file handler)
│   ├── examples.py          Three built-in demo organisations
│   ├── intelligence/
│   │   ├── __init__.py
│   │   └── org_loader.py    Registry + loader for all 12 intel orgs
│   └── webapp/
│       ├── __init__.py
│       ├── app.py           FastAPI application (5 routes)
│       └── templates/
│           └── index.html   Single-page web UI (dark mode, Chart.js)
├── examples/
│   ├── rare_earth_org.json              REE processing (JSON schema reference)
│   ├── us_national_security_architecture.json
│   ├── five_eyes/
│   │   ├── uk_national_security.json
│   │   ├── canada_national_security.json
│   │   ├── australia_national_security.json
│   │   └── new_zealand_national_security.json
│   └── adversarial/
│       ├── china_strategic_leadership.json
│       ├── russia_strategic_leadership.json
│       ├── iran_strategic_leadership.json
│       └── north_korea_strategic_leadership.json
├── tests/
│   ├── conftest.py                 Shared fixtures
│   ├── test_models.py              Role / Organization (51 tests)
│   ├── test_simulator.py           All 3 scenarios + helpers (44 tests)
│   ├── test_optimizer.py           BenchOptimizer (17 tests)
│   ├── test_reporting.py           JSON / console reporters (12 tests)
│   ├── test_reporting_html.py      HTML reporter + CLI integration (15 tests)
│   └── test_logging_config.py      Logging configuration (11 tests)
├── docs/
│   ├── architecture.md      Design decisions and data flow
│   ├── methodology.md       KPCI equations and model assumptions
│   ├── data_sources.md      Source calibration for built-in examples
│   ├── intelligence_orgs.md AO inversion, PASS Act context, sourcing policy
│   └── user_guide.md        Step-by-step CLI and API guide
├── .gitignore
├── CHANGELOG.md
├── CITATION.cff
├── LICENSE                  Apache 2.0
├── README.md
├── requirements.txt
└── setup.py
```

---

## Citation

```bibtex
@software{green2026kpvs,
  author  = {Green, Robert J.},
  title   = {{Key Person Vulnerability Simulator (KPVS)}},
  year    = {2026},
  version = {1.2.0},
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
ORCID: [0009-0002-9097-1021](https://orcid.org/0009-0002-9097-1021) |
SSRN: [ssrn.com/author=10825096](https://ssrn.com/author=10825096)
