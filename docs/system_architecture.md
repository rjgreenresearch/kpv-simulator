# System Architecture Document
# Key Person Vulnerability Simulator (KPVS)

**Document ID:** KPVS-SAD-001  
**Version:** 1.2.0  
**Status:** Released  
**Date:** May 2026  
**Author:** Robert J. Green, MTS Research Programme  
**Classification:** Unclassified / Public Release

---

## Table of Contents

1. [Architectural Overview](#1-architectural-overview)
2. [Design Principles](#2-design-principles)
3. [System Context](#3-system-context)
4. [Component Architecture](#4-component-architecture)
5. [Data Architecture](#5-data-architecture)
6. [Process Architecture](#6-process-architecture)
7. [Web Interface Architecture](#7-web-interface-architecture)
8. [Intelligence Org Module](#8-intelligence-org-module)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Security Architecture](#10-security-architecture)
11. [Extension Points](#11-extension-points)
12. [Architectural Decision Records](#12-architectural-decision-records)

---

## 1. Architectural Overview

KPVS is a layered Python application with three entry points — CLI, web
interface, and Python API — all operating over a shared simulation core.
The architecture is intentionally flat and dependency-minimal: the simulation
core has no runtime dependencies beyond the Python standard library, making it
suitable for air-gapped deployment.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Entry Points                             │
│                                                                 │
│   ┌──────────────┐   ┌──────────────────┐   ┌───────────────┐  │
│   │  CLI          │   │  Web Interface   │   │  Python API   │  │
│   │  main.py      │   │  webapp/app.py   │   │  import kpvs  │  │
│   └──────┬───────┘   └────────┬─────────┘   └───────┬───────┘  │
│          │                    │                      │          │
├──────────┼────────────────────┼──────────────────────┼──────────┤
│          │         Simulation Core                   │          │
│          ▼                    ▼                      ▼          │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  kpvs/                                                   │  │
│   │  ├── models.py       (Role, Organization, KPCI)          │  │
│   │  ├── simulator.py    (3 Monte Carlo scenarios)           │  │
│   │  ├── optimizer.py    (BenchOptimizer)                    │  │
│   │  └── examples.py     (3 built-in demo orgs)             │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                       Output Layer                              │
│                                                                 │
│   ┌─────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│   │  reporting.py   │  │reporting_html  │  │logging_config  │  │
│   │  Console + JSON │  │  HTML Reports  │  │  File + console│  │
│   └─────────────────┘  └────────────────┘  └────────────────┘  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    Intelligence Org Layer                       │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  kpvs/intelligence/                                      │  │
│   │  ├── org_loader.py   (registry + loader)                 │  │
│   │  └── examples/       (10 org JSON files)                 │  │
│   └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Design Principles

### 2.1 Zero-Dependency Core

The simulation core (`kpvs/models.py`, `kpvs/simulator.py`, `kpvs/optimizer.py`)
imports exclusively from the Python standard library. This is a hard architectural
constraint, not a convenience — it ensures the tool functions in air-gapped
national security environments without package installation, and it eliminates
supply-chain risk from third-party library updates.

### 2.2 Deterministic Reproducibility

Every simulation run is seeded with an explicit integer. The `random.Random`
instance is constructed fresh for each `KPVSimulator`, ensuring that runs
with identical `(seed, org, params)` produce byte-identical output regardless
of what other code has run in the same Python process. This is essential for
academic citation: Paper 5 results are reproducible by any researcher who
clones the repository.

### 2.3 Immutable Results

`SimulationResult` and `OptimizationResult` are dataclasses with all fields
set at construction time. They carry no reference to the `Organization` object
that produced them. This prevents results from silently changing if the
organisation is modified after simulation — a failure mode that would
invalidate academic citations.

### 2.4 Separation of Concerns

The simulation engine computes; the reporters format. Adding a new output
format (PDF, CSV, Markdown) requires only a new reporter class; no changes to
`simulator.py` are needed. Adding a new scenario requires only a new method on
`KPVSimulator`; no changes to the reporters are needed.

### 2.5 Fail-Fast Validation

The `Organisation.__post_init__` method validates all role references before
any simulation can begin. A simulation running on a structurally invalid
organisation would produce meaningless results; failing fast with a descriptive
error is more valuable than attempting graceful degradation.

---

## 3. System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                         Users                                   │
│                                                                 │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │
│  │ Researcher │  │Policy/Intel │  │     Developer             │  │
│  │ (CLI)      │  │ Analyst     │  │  (Python API / pytest)    │  │
│  │            │  │ (Web UI)    │  │                           │  │
│  └─────┬──────┘  └──────┬──────┘  └──────────┬───────────────┘  │
│        │                │                    │                  │
└────────┼────────────────┼────────────────────┼──────────────────┘
         │                │                    │
         ▼                ▼                    ▼
┌───────────────────────────────────────────────────────────────┐
│                        KPVS v1.2.0                            │
└───────────────────────────────────────────────────────────────┘
         │                │                    │
         ▼                ▼                    ▼
┌──────────────┐  ┌────────────────┐  ┌────────────────────────┐
│  File System │  │  Browser       │  │  Downstream pipeline   │
│  runs/       │  │  (HTML reports)│  │  (JSON output)         │
│  reports/    │  │                │  │                        │
│  logs/       │  │                │  │                        │
└──────────────┘  └────────────────┘  └────────────────────────┘
```

KPVS has no external service dependencies. It reads organisation data from
JSON files on disk, performs in-process computation, and writes output to disk.
The web interface serves requests synchronously — there is no message queue,
task queue, or external compute service.

---

## 4. Component Architecture

### 4.1 kpvs/models.py — Data Models

**Responsibility:** Define the Role and Organization data structures, validate
KPCI components, compute derived attributes (kpci, tier, estimated_restoration_months),
and provide JSON serialisation/deserialisation.

**Key Classes:**

`Role` (dataclass)
- Stores KPCI components and org graph position
- `__post_init__` validates all three components ∈ [0,4], capability_weight > 0,
  bench_depth ≥ 0
- Computes kpci and tier as derived attributes
- Computes estimated_restoration_months as a property (not stored)

`Organization` (dataclass)
- Stores the role graph as a dict[str, Role]
- `__post_init__` validates all role references (mission_critical_roles,
  reports_to, critical_dependencies)
- Provides graph query methods: get_dependents(), get_subordinates(),
  roles_by_kpci(), tier_summary()

**Dependencies:** Standard library only (`dataclasses`, `logging`, `typing`)

### 4.2 kpvs/simulator.py — Monte Carlo Engine

**Responsibility:** Execute stochastic capability degradation scenarios and
return distributional statistics.

**Key Classes and Functions:**

`_capability_after_loss(org, lost_ids)` — Pure function computing residual
capability for a given set of lost roles. No state; safe to call from any context.

`_build_result(...)` — Factory function constructing a SimulationResult from
a distribution list. Computes all percentiles once; never recomputes.

`KPVSimulator`
- Owns a seeded `random.Random` instance created once at construction
- Three scenario methods, each accepting n_losses and n_iterations
- KPCI report generation (no Monte Carlo; pure computation)

`SimulationResult` (dataclass, effectively immutable)
- Distributional statistics + scenario metadata + extra dict
- `to_dict()` for JSON serialisation

**Dependencies:** `kpvs.models`, standard library (`random`, `statistics`,
`dataclasses`, `datetime`, `typing`)

### 4.3 kpvs/optimizer.py — Bench Optimiser

**Responsibility:** Allocate a budget of bench-depth investments to maximise
expected capability retention under adversarial targeting.

**Algorithm:** Greedy marginal improvement. For each budget unit:
1. For each role below max_bench, temporarily increment bench_depth
2. Run adversarial scenario at reduced iterations (eval_iterations)
3. Score improvement weighted by KPCI/12
4. Commit to highest-scoring role; restore all others

**Key Design Choice:** The optimiser modifies `org.roles[x].bench_depth`
in-place during evaluation and then restores it. Callers who need
reproducibility must pass a `copy.deepcopy(org)` — this is documented
as a contract in the module docstring and tested in `test_optimizer.py`.

**Dependencies:** `kpvs.models`, `kpvs.simulator._capability_after_loss`,
standard library

### 4.4 kpvs/reporting.py — Console and JSON Output

**Responsibility:** Format simulation results for human-readable console output
and machine-readable JSON artefacts.

`ConsoleReporter` — Stateful object holding org and sim references; methods
produce formatted terminal output (KPCI table, scenario table, cascade cards,
optimiser table, recommendations, header/footer).

`JSONReporter` — Stateless; writes JSON files to a configured directory.
`write_summary()` writes the unified artefact consumed by the HTML reporter.

### 4.5 kpvs/reporting_html.py — HTML Report Generator

**Responsibility:** Produce self-contained HTML reports from KPVS summary dicts.

`_build_single_report(data)` — Pure function; accepts a summary dict,
returns an HTML string. Chart data is embedded as JSON literals in `<script>` tags.
All user-supplied strings are HTML-escaped via `_esc()`.

`_build_comparative_report(summaries, set_name)` — Aggregates multiple
summary dicts into a cross-organisation comparison report.

`HTMLReporter` — Thin wrapper managing output directory and calling the
builder functions.

**External dependency:** Chart.js 4.4.1 loaded from cdnjs at report *view* time.
The HTML file itself is static and portable; Chart.js renders when opened
in a browser.

### 4.6 kpvs/logging_config.py — Logging

**Responsibility:** Configure the root logger with console and rotating file
handlers. Exported `configure_logging()` is called once at application startup;
`get_run_logger(run_id)` returns child loggers namespaced to specific runs.

Log levels by layer:
- `INFO` — run-level events (org loaded, scenarios completed, files written)
- `DEBUG` — per-2500-iteration progress, internal state
- `WARNING` — handled edge cases (missing org files, at-max bench)
- `ERROR` — unrecoverable conditions that still allow partial output

### 4.7 kpvs/examples.py — Built-in Organisations

**Responsibility:** Construct the three canonical example organisations
programmatically. These are the authoritative reference implementations of the
org schema and are used as fixtures in the test suite.

### 4.8 kpvs/intelligence/org_loader.py — Intelligence Org Registry

**Responsibility:** Maintain the file-path registry for all 10 intelligence
org JSON files, load them into Organization objects, and expose predefined
org sets.

**Registry pattern:** `ORG_REGISTRY` is a dict[str, Path] mapping short keys
(e.g. `"cn"`) to absolute paths. `ORG_SETS` maps set names to lists of keys.
This keeps the path logic in one place; adding a new org requires only one
line in `ORG_REGISTRY`.

**Adversarial flag propagation:** `load_org()` attaches `_adversarial` and
`_ao_note` as runtime attributes on the Organization object after loading.
These are not part of the dataclass schema to avoid polluting the data model
with operational metadata.

### 4.9 kpvs/webapp/app.py — FastAPI Application

**Responsibility:** Serve the web UI and expose the simulation API. See
Section 7 for detailed web interface architecture.

---

## 5. Data Architecture

### 5.1 Primary Data Flow

```
User supplies org JSON
        │
        ▼
Organization.from_dict()    ← validates structure
        │
        ▼
KPVSimulator(org, seed)     ← seeds RNG
        │
        ├── scenario_random_attrition()     ┐
        ├── scenario_adversarial_targeting()├── SimulationResult × 3+
        └── scenario_cascade_failure()      ┘
                │
                ▼
        BenchOptimizer.optimise()           ← OptimizationResult
                │
                ▼
        JSONReporter.write_summary()        ← summary.json
                │
                ▼
        HTMLReporter.write_report()         ← report.html
```

### 5.2 State Lifecycle

KPVS is a stateless computation engine. The only persistent state is:
1. **Input:** org JSON files in `examples/`
2. **Output:** run artefacts in `runs/` and `reports/`
3. **Logs:** rotating logs in `logs/`

The web interface maintains no server-side session state. Each `/api/run`
request is fully self-contained: the org data is sent in the request body,
the simulation runs synchronously, artefacts are written to disk, and the
result (including the report URL) is returned in the response.

### 5.3 File System Layout

```
kpv-simulator/                    ← project root
├── examples/                     ← read-only reference org JSON files
│   ├── rare_earth_org.json
│   ├── us_national_security_architecture.json
│   ├── five_eyes/
│   └── adversarial/
├── runs/                         ← JSON artefacts (created at runtime)
│   └── <label>_YYYYMMDD_HHMMSS/
│       └── <run_id>_*.json
├── reports/                      ← HTML reports (created at runtime)
│   └── <label>_YYYYMMDD_HHMMSS/
│       └── <run_id>_report.html
└── logs/                         ← rotating log files (created at runtime)
    └── kpvs_YYYYMMDD_HHMMSS.log
```

---

## 6. Process Architecture

### 6.1 CLI Process Flow

```
main()
  ├── configure_logging()
  ├── Build reporters (timestamped subdirs)
  ├── If intel mode: run_intel_mode()
  │     ├── load_org() or load_org_set()
  │     └── run_simulation() × N orgs
  │           └── [see below]
  └── Else: resolve org(s)
        └── run_simulation() × N orgs

run_simulation(org, args, json_reporter, html_reporter)
  ├── KPVSimulator(org, seed)
  ├── sim.kpci_report()
  ├── sim.scenario_random_attrition()
  ├── sim.scenario_adversarial_targeting()
  ├── [sim.scenario_cascade_failure() × MC roles]
  ├── [BenchOptimizer.optimise()]
  ├── json_reporter.write_summary()      → summary.json
  └── html_reporter.write_report()       → report.html
```

### 6.2 Simulation Iteration Loop

Each Monte Carlo scenario follows the same structure:

```
for i in range(n_iterations):
    lost = select_lost_roles(rng, org, n_losses, scenario_params)
    cap  = _capability_after_loss(org, lost)
    distribution.append(cap / org.total_capability * 100)

return _build_result(distribution, metadata)
```

`_capability_after_loss` is a pure function with O(|roles|) complexity.
Total scenario complexity: O(N × |roles|). For N=10,000 and |roles|=50,
this is 500,000 dict lookups — sub-second on any modern hardware.

### 6.3 Cascade Propagation Algorithm

```
queue = [dependents of trigger_role]
visited = {trigger_role_id}
lost = [trigger_role_id]

while queue:
    dep = queue.pop(0)
    if dep.id in visited: continue
    visited.add(dep.id)

    p_fail = (dep.DR / 4.0) × 0.70 × max(0.10, 1.0 - dep.bench_depth × 0.40)

    if rng.random() < p_fail:
        lost.append(dep.id)
        queue.extend(dependents_of(dep) not in visited)

residual = _capability_after_loss(org, lost)
```

This is a breadth-first stochastic traversal. The `visited` set prevents
infinite loops in cyclic dependency structures (which are invalid per FR-005
but could theoretically be constructed via direct dict manipulation).

---

## 7. Web Interface Architecture

### 7.1 Component Diagram

```
Browser (SPA)                  FastAPI Server
─────────────────              ──────────────────────────────────
index.html                     kpvs/webapp/app.py
  ├── Sidebar                  ├── GET /            → templates/index.html
  │   └── fetch /api/orgs      ├── GET /api/orgs    → list org metadata
  ├── Org Editor               ├── GET /api/orgs/{key} → org JSON
  │   └── inline JS state      ├── POST /api/run    → SimulationResult + report URL
  ├── Params Panel             ├── GET /api/runs    → run history
  └── Results Tab              └── GET /reports/... → StaticFiles mount
      ├── fetch /api/run
      └── <iframe src="/reports/...">
```

### 7.2 API Request/Response Contract

**POST /api/run**

Request body (JSON):
```json
{
  "org_data": { /* full org JSON, may be user-edited */ },
  "org_key": "rare_earth",
  "params": {
    "iterations": 10000,
    "seed": 20260501,
    "n_losses": null,
    "budget": 3,
    "targeting_accuracy": 0.85,
    "skip_cascade": false,
    "skip_optimizer": false
  }
}
```

Response (JSON):
```json
{
  "run_id": "run_20260502_075452",
  "run_folder": "rare_earth_run_20260502_075452",
  "report_url": "/reports/rare_earth_run_20260502_075452/run_20260502_075452_report.html",
  "json_dir": "/absolute/path/to/runs/rare_earth_run_20260502_075452",
  "summary": { /* full KPVS summary dict */ },
  "adversarial_gap_pp": 17.9
}
```

### 7.3 Client-Side State Management

The web UI uses a plain JavaScript object (`state`) as its single source of truth:
```javascript
const state = {
  orgData:    null,   // current org JSON (may be user-edited)
  orgKey:     null,   // key of the loaded org
  lastResult: null,   // most recent run result
};
```

Org edits mutate `state.orgData` directly; the `renderOrgEditor()` and
`renderOrgCards()` functions re-render affected DOM sections. KPCI recalculation
is synchronous (pure arithmetic) and occurs on every input event.

The full `state.orgData` is sent to `/api/run` on simulation execution,
meaning any user edits — including KPCI changes, new roles, or deleted roles —
are reflected in the simulation without a separate save step.

### 7.4 Synchronous Execution Model

Because KPVS simulations complete in under a second, the web server executes
them synchronously within the FastAPI request handler. There is no task queue,
background worker, or WebSocket progress stream. If future requirements include
N > 100,000 iterations, an async background task with progress polling would
be appropriate.

---

## 8. Intelligence Org Module

### 8.1 Design

The intelligence org module is an optional extension layer. The simulation
core has no knowledge of it — `org_loader.py` loads JSON files and returns
standard `Organization` objects. The only intelligence-specific behaviour is:

1. The `adversarial_org` flag propagated as a runtime attribute for the HTML
   reporter's AO inversion banner
2. The `ao_note` string passed through to HTML reports

This design means the intelligence org module can be disabled, removed, or
replaced without any changes to the simulation core.

### 8.2 AO Inversion

For adversarial organisations, the Adversarial Observability (AO) component
is semantically inverted:

| Context | AO meaning |
|---------|-----------|
| Allied org | How visible is this role to a foreign adversary? |
| Adversarial org | How visible is this role to allied OSINT? |

A low AO score on a Chinese MSS role (AO=1.5) does not mean the MSS director
is hard to replace — it means allied analysts have poor visibility into that
role's criticality from open sources. The near-zero adversarial targeting gap
that results is an **intelligence gap finding**: the simulator cannot outperform
random selection because it cannot rank targets without visibility.

This is architecturally significant: the same model produces different
analytical conclusions depending on the `adversarial_org` flag, without any
changes to the simulation mathematics.

---

## 9. Deployment Architecture

### 9.1 Local Research Deployment (Default)

```
Researcher laptop
└── python start_webapp.py
    ├── Binds 127.0.0.1:8000
    ├── Serves web UI to local browser
    └── Writes artefacts to local filesystem
```

No authentication, no TLS, no external services. Suitable for individual
research use and local policy analysis sessions.

### 9.2 Shared Analysis Server

```
Analysis server (internal network)
└── python start_webapp.py --host 0.0.0.0 --port 8080
    └── Behind institutional reverse proxy
        ├── TLS termination at proxy
        ├── Authentication at proxy (recommended)
        └── Rate limiting at proxy (recommended)
```

For multi-analyst use, the shared filesystem for `runs/` and `reports/` allows
all users to see each other's run history. If isolation is required, separate
server instances with separate working directories are recommended.

### 9.3 Air-Gapped CLI Deployment

```
Air-gapped workstation
└── python main.py --example rare_earth \
                   --iterations 10000   \
                   --json-dir /output/  \
                   --no-log-file
```

No network access required. HTML reports will not render Chart.js charts
unless Chart.js is bundled locally and the template is modified to use a
local path. The console and JSON outputs are fully functional offline.

---

## 10. Security Architecture

### 10.1 Input Validation

All org data submitted to `/api/run` is passed through `Organization.from_dict()`,
which validates:
- All KPCI components ∈ [0, 4] (raises ValueError → HTTP 422)
- All role references exist (raises ValueError → HTTP 422)
- capability_weight > 0, bench_depth ≥ 0

Pydantic validates `SimParams` before the org data is touched:
- iterations ∈ [100, 100,000]
- targeting_accuracy ∈ (0.01, 1.0]
- budget ∈ [0, 20]

### 10.2 Output Sanitisation

`reporting_html.py` applies `_esc()` (HTML entity escaping) to all
user-supplied strings before insertion into HTML:
- `org.name` → HTML title and header
- `role.title` → KPCI table cells
- `role.recommendation` → Recommendations section
- `result.scenario` → Scenario table labels

This prevents stored XSS in generated HTML reports, which are served as
static files and may be opened by other users.

### 10.3 File System Boundaries

The FastAPI static file mount serves **only** the `reports/` directory:
```python
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")
```
No other directory is served. Path traversal attacks against `/reports/../etc/`
are blocked by Starlette's StaticFiles implementation.

Run artefacts are written to `runs/<label>_timestamp/` and `reports/<label>_timestamp/`.
The label is derived from the `org_key` field in the API request, which is used
only as a directory name prefix. Path separators and special characters in `org_key`
could create unexpected paths; this is a known limitation for the open-source release.

---

## 11. Extension Points

### 11.1 Adding a New Simulation Scenario

1. Add a new method to `KPVSimulator` in `kpvs/simulator.py`:
   ```python
   def scenario_new_scenario(self, ...) -> SimulationResult:
       dist = []
       for i in range(n_iterations):
           lost = [...]  # your selection logic
           dist.append(self._pct(_capability_after_loss(self.org, lost)))
       return _build_result("New Scenario", self.run_id, ...)
   ```
2. Add the call to `run_simulation()` in `main.py` and `/api/run` in `webapp/app.py`
3. Add tests in `tests/test_simulator.py`

No changes to `models.py`, `optimizer.py`, or `reporting.py` are required.

### 11.2 Adding a New Intelligence Org

1. Create a JSON file in `examples/five_eyes/` or `examples/adversarial/`
   following the schema in Section 5 of the SRS
2. Add one line to `ORG_REGISTRY` in `kpvs/intelligence/org_loader.py`:
   ```python
   "jp": ROOT / "examples" / "five_eyes" / "japan_national_security.json",
   ```
3. Add the key to the appropriate entry in `ORG_SETS`
4. Add the key to `INTEL_ORG_KEYS` in `kpvs/webapp/app.py`

### 11.3 Adding a New Output Format

Create a new reporter class in the `kpvs/` package accepting a summary dict
and writing output. Register it in `run_simulation()` in `main.py`. No changes
to the simulation core are required.

### 11.4 Classified Deployment

For a classified implementation with IC-quality AO data:

1. Replace the `examples/` JSON files with classified versions containing
   higher-fidelity AO scores
2. The simulation mathematics are unchanged; only the input data changes
3. The `ao_note` field in adversarial org JSON should be updated to reflect
   the data source classification
4. All output directories should be on classified storage

The simulation core requires no modification for classified deployment.

---

## 12. Architectural Decision Records

### ADR-001: Pure Standard Library for Simulation Core

**Decision:** The `kpvs/` package (excluding `kpvs/webapp/`) imports only
from the Python standard library.

**Rationale:** Air-gapped deployment compatibility; zero supply-chain risk
from third-party library updates; simplest possible installation for
non-technical researchers.

**Consequence:** NumPy's vectorised operations are unavailable, limiting
performance for very large orgs or very large N. Mitigated by the observation
that typical orgs have ≤50 roles and N=10,000 completes in under a second
with pure Python.

### ADR-002: Greedy Optimiser Over Exhaustive Search

**Decision:** BenchOptimizer uses greedy marginal improvement, not exhaustive
search or MILP.

**Rationale:** Exhaustive search over B units allocated to R roles is
O(R^B) — infeasible for R=20, B=10. MILP adds a solver dependency. The greedy
approach finds near-optimal solutions (within 5-10% of optimal in empirical
testing) in O(B × R × eval_iterations) time.

**Consequence:** Optimiser may miss globally optimal allocations. Documented
as a limitation in `docs/methodology.md`.

### ADR-003: Synchronous Web API

**Decision:** `/api/run` executes simulations synchronously within the request
handler.

**Rationale:** KPVS simulations complete in under one second. The complexity
of an async task queue (Celery, Redis, WebSocket polling) is not justified.

**Consequence:** Server blocks on simulation execution for the duration of
the request. Acceptable for the current use case; see Section 7.4 for the
recommended upgrade path if N > 100,000 is required.

### ADR-004: Flat File Persistence Over Database

**Decision:** All run artefacts are stored as flat JSON files in timestamped
directories.

**Rationale:** No database engine dependency; artefacts are human-readable
and portable; run history is reconstructable from the filesystem. Consistent
with the air-gap deployment constraint.

**Consequence:** Run history requires directory scanning (`GET /api/runs`
iterates `reports/`), which degrades with very large run counts. Mitigated
by the `limit` parameter (default 20 most recent).

### ADR-005: Immutable SimulationResult

**Decision:** SimulationResult is a dataclass with all fields set at
construction time.

**Rationale:** Results must be stable for academic citation. A mutable result
that could be modified after construction would invalidate the reproducibility
guarantee.

**Consequence:** The extra dict is mutable (it is a plain dict). Future
versions should consider making extra a frozen mapping.

---

*KPVS SAD-001 v1.2.0 — MTS Research Programme — Robert J. Green — May 2026*
