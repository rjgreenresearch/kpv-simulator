# Software Requirements Specification
# Key Person Vulnerability Simulator (KPVS)

**Document ID:** KPVS-SRS-001  
**Version:** 1.2.0  
**Status:** Released  
**Date:** May 2026  
**Author:** Robert J. Green, MTS Research Programme  
**Classification:** Unclassified / Public Release

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Stakeholders and User Classes](#3-stakeholders-and-user-classes)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [External Interface Requirements](#6-external-interface-requirements)
7. [Data Requirements](#7-data-requirements)
8. [Constraints and Assumptions](#8-constraints-and-assumptions)
9. [Acceptance Criteria](#9-acceptance-criteria)
10. [Traceability Matrix](#10-traceability-matrix)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the functional and
non-functional requirements for the Key Person Vulnerability Simulator (KPVS),
an open-source Monte Carlo simulation tool for quantifying human capital
concentration risk in organizational networks. The document is intended for
developers contributing to the project, researchers adapting the tool for
related domains, and institutional users evaluating KPVS for integration into
security assessment workflows.

### 1.2 Scope

KPVS is a Python application providing:

- A command-line interface (CLI) for batch simulation and reproducible research runs
- A web interface (FastAPI) for interactive organizational editing and parameter exploration
- Programmatic Python APIs for integration into research pipelines
- Self-contained HTML report generation for dissemination to non-technical audiences

KPVS is **not** a data collection tool, a classified intelligence system, or a
personnel management system. It is an analytical modelling framework that
operates on data the user supplies.

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|-----------|
| AO | Adversarial Observability — KPCI component measuring external identifiability |
| CONOPS | Concept of Operations |
| DR | Documentation Ratio — KPCI component measuring tacit knowledge concentration |
| HUMINT | Human Intelligence |
| KPCI | Key Person Concentration Index — composite vulnerability score (0–12) |
| KPV | Key Person Vulnerability — structural condition meeting three defined criteria |
| KPVS | Key Person Vulnerability Simulator — this application |
| MC | Mission-Critical — role designation triggering cascade analysis |
| MTS | Mutual Threshold Saturation — parent research framework |
| OSINT | Open-Source Intelligence |
| PASS Act | Protecting American Security from Kremlin Aggression Act |
| pp | Percentage points |
| SRS | Software Requirements Specification |
| ST | Substitution Timeline — KPCI component measuring succession difficulty |
| TRL | Technology Readiness Level |

### 1.4 References

| Document | Description |
|----------|-------------|
| Green, R.J. (2026). MTS Working Paper 5 | "The Irreplaceable Node" — theoretical basis |
| `docs/methodology.md` | KPCI equations and model assumptions |
| `docs/architecture.md` | System design and data flow |
| `docs/intelligence_orgs.md` | Intelligence org sourcing and AO inversion policy |
| `CITATION.cff` | Canonical software citation format |
| Apache 2.0 License | `LICENSE` in project root |

---

## 2. Overall Description

### 2.1 Product Perspective

KPVS is a standalone application within the MTS Research Programme tool suite,
which also includes the Cost-Asymmetry Simulator (CAS) and the Economic
Fragility Simulator. All three tools share the same Python-first, zero-runtime-
dependency design philosophy and produce JSON and HTML artefacts for research
dissemination.

KPVS extends the MTS programme's material supply chain dependency analysis
(Paper 4) to the human capital domain, applying the same single-source
concentration framework to individual roles rather than material inputs.

### 2.2 Product Functions

At the highest level, KPVS performs four functions:

1. **KPCI Scoring** — Accept an organizational role graph and compute the
   Key Person Concentration Index for each role.
2. **Monte Carlo Simulation** — Run stochastic capability degradation scenarios
   under three adversarial conditions across N iterations.
3. **Bench Investment Optimisation** — Identify the optimal allocation of a
   fixed budget of succession-depth investments to maximise capability
   retention under adversarial targeting.
4. **Report Generation** — Produce human-readable reports (console, JSON, HTML)
   suitable for research citation and policy dissemination.

### 2.3 Operating Environment

- **Runtime:** Python 3.10 or later on Windows, macOS, or Linux (x86-64 or ARM64)
- **CLI mode:** No external dependencies beyond the Python standard library
- **Web interface:** Requires FastAPI, Uvicorn, Jinja2, python-multipart
- **Test environment:** Requires pytest and httpx
- **Browser:** Any modern browser (Chrome 90+, Firefox 88+, Edge 90+, Safari 14+)
  for the web interface and HTML reports

### 2.4 Design and Implementation Constraints

- **Air-gap compatibility:** CLI mode must function with zero network access.
  The HTML report template loads Chart.js from cdnjs.cloudflare.com; this is
  the only external dependency and is acceptable for connected deployments only.
- **No persistent database:** All state is stored in flat JSON files. No
  database engine is required or permitted.
- **Pure standard library for simulation core:** The `kpvs/` package (excluding
  `kpvs/webapp/`) must not import any package outside the Python standard library.
- **Reproducibility:** Every simulation run must produce identical output given
  the same seed, org data, and parameters.

---

## 3. Stakeholders and User Classes

### 3.1 Primary Users

| User Class | Description | Primary Interface |
|-----------|-------------|-------------------|
| Academic Researcher | Runs canonical simulations for paper citations; extends the model | CLI |
| Policy Analyst | Analyses specific organisations; generates reports for briefings | Web UI |
| Security Practitioner | Assesses their own organisation's KPV architecture | Web UI |
| Intelligence Analyst | Applies KPCI framework to adversarial or allied structures | CLI + Web UI |
| Software Developer | Contributes to the codebase; integrates KPVS into pipelines | Python API |

### 3.2 Secondary Stakeholders

- **MTS Research Programme** — Primary theoretical framework context
- **CSIS, Atlantic Council, RAND** — Potential institutional partners using
  the tool in policy reports
- **DoD / IC users** — Potential classified implementations with higher-fidelity
  AO data (not within scope of this open-source release)

---

## 4. Functional Requirements

Requirements are identified as `FR-XXX`. Priority is High (H), Medium (M),
or Low (L). Version indicates the release in which the requirement was
first satisfied.

### 4.1 Data Model Requirements

| ID | Requirement | Priority | Version |
|----|-------------|----------|---------|
| FR-001 | The system SHALL represent an organisation as a directed graph of Role nodes with typed edges (reports_to, critical_dependencies). | H | 1.0.0 |
| FR-002 | Each Role SHALL carry three KPCI component scores (ST, DR, AO), each constrained to the closed interval [0, 4]. | H | 1.0.0 |
| FR-003 | The system SHALL reject Role construction if any KPCI component is outside [0, 4], raising a ValueError with the component name and invalid value. | H | 1.0.0 |
| FR-004 | The system SHALL compute KPCI = ST + DR + AO and classify each Role into one of four tiers: Tier-1 KPV (≥10), Tier-2 KPV (≥7), Manageable (≥4), Resilient (<4). | H | 1.0.0 |
| FR-005 | The system SHALL validate all dependency references on Organisation construction, raising ValueError for references to undefined role IDs. | H | 1.0.0 |
| FR-006 | The system SHALL support serialisation of Organization objects to and from JSON dictionaries using to_dict() and from_dict() with round-trip fidelity. | H | 1.0.0 |
| FR-007 | Roles SHALL support an optional bench_depth integer (≥0) representing identified successors in active development. | H | 1.0.0 |
| FR-008 | Roles SHALL support an optional capability_weight float (>0) representing relative organisational capability contribution. | H | 1.0.0 |

### 4.2 Simulation Requirements

| ID | Requirement | Priority | Version |
|----|-------------|----------|---------|
| FR-010 | The system SHALL implement a random attrition scenario removing N roles uniformly at random across M iterations. | H | 1.0.0 |
| FR-011 | The system SHALL implement an adversarial targeting scenario removing N roles with preferential KPCI-ranked selection at configurable accuracy P ∈ (0, 1]. | H | 1.0.0 |
| FR-012 | The system SHALL implement a cascade failure scenario stochastically propagating capability loss from a single trigger role to its dependents. | H | 1.0.0 |
| FR-013 | The cascade failure propagation probability for each dependent SHALL be: p_fail = (DR/4.0) × 0.70 × max(0.10, 1.0 − bench_depth × 0.40). | H | 1.0.0 |
| FR-014 | The capability model SHALL award bench_depth > 0 roles partial capability: min(1.0, bench_depth × 0.75) × capability_weight. | H | 1.0.0 |
| FR-015 | The capability model SHALL degrade cascade-affected (but non-lost) dependents of mission-critical roles to 0.50 × capability_weight. | H | 1.0.0 |
| FR-016 | All scenarios SHALL accept an integer seed parameter and produce identical output for identical (seed, org, params) inputs. | H | 1.0.0 |
| FR-017 | Each scenario SHALL return a SimulationResult containing: mean, median, standard deviation, min, max, P10, P25, P75, P90 capability percentages. | H | 1.0.0 |
| FR-018 | The adversarial targeting scenario SHALL record targeting_accuracy in the result extra dict. | M | 1.0.0 |
| FR-019 | The cascade failure scenario SHALL record trigger_role_id, trigger_kpci, trigger_tier, and estimated_restoration_months in the result extra dict. | M | 1.0.0 |
| FR-020 | The n_losses=0 parameter SHALL produce 100% mean capability (no roles lost). | H | 1.1.0 |

### 4.3 Optimiser Requirements

| ID | Requirement | Priority | Version |
|----|-------------|----------|---------|
| FR-030 | The system SHALL implement a greedy marginal-improvement bench investment optimiser allocating B bench units to maximise adversarial scenario mean capability. | H | 1.0.0 |
| FR-031 | The optimiser SHALL weight marginal improvement by KPCI/12 to prefer allocation to high-vulnerability roles. | H | 1.0.0 |
| FR-032 | The optimiser SHALL respect a configurable max_bench_per_role ceiling (default 5). | M | 1.0.0 |
| FR-033 | The optimiser SHALL return an OptimizationResult containing: allocation dict, baseline_mean_pct, optimized_mean_pct, improvement_pp. | H | 1.0.0 |

### 4.4 Reporting Requirements

| ID | Requirement | Priority | Version |
|----|-------------|----------|---------|
| FR-040 | The system SHALL produce a KPCI tabular report for all roles sorted by descending KPCI score. | H | 1.0.0 |
| FR-041 | The system SHALL produce JSON artefacts for each simulation result, the KPCI report, the optimiser result, and a unified summary. | H | 1.0.0 |
| FR-042 | JSON artefacts SHALL be valid UTF-8 encoded JSON with 2-space indentation. | M | 1.0.0 |
| FR-043 | The system SHALL produce self-contained single-file HTML reports that render correctly in any modern browser without a server. | H | 1.1.0 |
| FR-044 | HTML reports SHALL include: KPCI table, KPCI bar chart, tier distribution chart, capability distribution comparison chart, cascade failure cards, optimiser results, and priority recommendations. | H | 1.1.0 |
| FR-045 | HTML reports for adversarial organisations SHALL display an AO inversion warning banner. | H | 1.1.0 |
| FR-046 | The system SHALL produce a multi-organisation comparative HTML report for org-set runs. | H | 1.1.0 |
| FR-047 | CLI output directories SHALL be timestamped subdirectories in the format `<label>_YYYYMMDD_HHMMSS/`. | M | 1.2.0 |

### 4.5 CLI Requirements

| ID | Requirement | Priority | Version |
|----|-------------|----------|---------|
| FR-050 | The CLI SHALL support `--demo`, `--example`, `--org`, `--intel-org`, `--org-set`, and `--list-orgs` as mutually exclusive source flags. | H | 1.1.0 |
| FR-051 | The CLI SHALL support `--iterations`, `--seed`, `--n-losses`, `--budget`, `--targeting-accuracy`, `--skip-cascade`, `--skip-optimizer`. | H | 1.0.0 |
| FR-052 | The CLI SHALL support `--json-dir` and `--html-dir` for output artefact directories. | H | 1.1.0 |
| FR-053 | The CLI SHALL support `--log-level`, `--log-file`, and `--no-log-file`. | M | 1.0.0 |
| FR-054 | The `--list-orgs` flag SHALL print all registry keys with file-exists status and all org-set names, then exit with code 0. | M | 1.1.0 |

### 4.6 Web Interface Requirements

| ID | Requirement | Priority | Version |
|----|-------------|----------|---------|
| FR-060 | The web interface SHALL serve a single-page application at `GET /`. | H | 1.2.0 |
| FR-061 | `GET /api/orgs` SHALL return metadata (key, group, name, role count, tier counts) for all available organisations. | H | 1.2.0 |
| FR-062 | `GET /api/orgs/{key}` SHALL return the full JSON for a named organisation. | H | 1.2.0 |
| FR-063 | `POST /api/run` SHALL accept an org_data dict and SimParams, execute a full simulation, write artefacts to timestamped subdirectories, and return the summary dict and report URL. | H | 1.2.0 |
| FR-064 | `GET /api/runs` SHALL return run history metadata, most recent first, by scanning the reports directory. | M | 1.2.0 |
| FR-065 | The web UI SHALL provide inline-editable KPCI component fields; KPCI score and tier colour SHALL update in real time on input. | H | 1.2.0 |
| FR-066 | The web UI SHALL allow users to add roles, delete roles, and toggle mission-critical status without a page reload. | H | 1.2.0 |
| FR-067 | The web UI SHALL allow upload of a custom org JSON file. | M | 1.2.0 |
| FR-068 | The web UI SHALL display simulation results including Chart.js visualisations and embed the HTML report in an iframe on the Results tab. | H | 1.2.0 |
| FR-069 | The web server SHALL create timestamped subdirectories matching the CLI convention: `reports/<label>_YYYYMMDD_HHMMSS/`. | H | 1.2.0 |

### 4.7 Intelligence Org Requirements

| ID | Requirement | Priority | Version |
|----|-------------|----------|---------|
| FR-070 | The system SHALL include open-source KPV assessments for 10 organisations: us_nsa, uk, ca, au, nz, cn, ru, ir, kp, and the rare_earth example. | H | 1.1.0 |
| FR-071 | Adversarial org JSON files SHALL include an `adversarial_org: true` flag and an `ao_note` field documenting the AO inversion. | H | 1.1.0 |
| FR-072 | The intelligence org module SHALL support predefined org sets: five_eyes, adversarial, all_intel, us_and_china. | H | 1.1.0 |
| FR-073 | All intelligence org data SHALL be sourced exclusively from publicly available documents. Sources SHALL be cited in the notes field of each role. | H | 1.1.0 |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| ID | Requirement |
|----|-------------|
| NFR-001 | A 10,000-iteration simulation on an organisation with ≤50 roles SHALL complete in under 10 seconds on a modern laptop (2GHz+ single core). |
| NFR-002 | The web interface `/api/run` endpoint SHALL return within 15 seconds for N=10,000 on an organisation with ≤50 roles. |
| NFR-003 | KPCI report generation SHALL complete in under 100ms regardless of org size. |

### 5.2 Reliability

| ID | Requirement |
|----|-------------|
| NFR-010 | The simulation engine SHALL produce byte-identical results for identical (seed, org, params) inputs across platforms. |
| NFR-011 | Invalid KPCI scores, missing role references, and malformed JSON SHALL produce descriptive error messages, never silent incorrect results. |
| NFR-012 | All 140 unit and integration tests SHALL pass on Windows, macOS, and Linux with Python 3.10+. |

### 5.3 Security

| ID | Requirement |
|----|-------------|
| NFR-020 | The web interface SHALL sanitise all user-supplied org data before passing it to Organisation.from_dict(). Invalid data SHALL return HTTP 422 with a descriptive message. |
| NFR-021 | HTML report generation SHALL HTML-escape all user-supplied strings (org names, role titles, notes) to prevent XSS in generated reports. |
| NFR-022 | The web server SHALL NOT expose any file system paths beyond the `reports/` directory via the static file mount. |
| NFR-023 | The application SHALL NOT log or store user-supplied KPCI data beyond the configured run directory. |

### 5.4 Maintainability

| ID | Requirement |
|----|-------------|
| NFR-030 | Each module SHALL have a module-level docstring describing its purpose, key classes, and usage pattern. |
| NFR-031 | Public API functions SHALL have type annotations on all parameters and return values. |
| NFR-032 | Adding a new simulation scenario SHALL require changes to simulator.py only; no changes to reporting.py, optimizer.py, or main.py SHALL be required. |
| NFR-033 | CHANGELOG.md SHALL be updated for every version increment. |

### 5.5 Portability

| ID | Requirement |
|----|-------------|
| NFR-040 | The CLI mode SHALL function in air-gapped environments with no network access. |
| NFR-041 | The project SHALL not use platform-specific APIs or path separators in any source file. |
| NFR-042 | Generated HTML reports SHALL be renderable offline (Chart.js loads from cdnjs; an offline fallback is acceptable for air-gapped use). |

### 5.6 Usability

| ID | Requirement |
|----|-------------|
| NFR-050 | The web UI SHALL display a meaningful toast notification within 500ms of any user action that changes state (org load, edit, run complete, error). |
| NFR-051 | The CLI SHALL print a structured summary to stdout within 2 seconds of run completion even for N=10,000. |
| NFR-052 | Error messages SHALL identify the specific role ID and parameter name involved in any validation failure. |

---

## 6. External Interface Requirements

### 6.1 User Interfaces

The system provides two user interfaces:

**CLI** — Standard POSIX-style argument interface via Python argparse. Produces
structured console output parseable by downstream tools. Exit codes: 0 (success),
1 (argument error), 2 (runtime error).

**Web UI** — Single-page application served at `http://localhost:8000`. Dark-mode
dashboard with sidebar, tabbed main panel, and inline Chart.js visualisations.
Compatible with screen readers via semantic HTML (role attributes, ARIA labels
on interactive elements).

### 6.2 Software Interfaces

**FastAPI / Uvicorn** — Web framework and ASGI server. Version ≥ 0.100 / ≥ 0.23.

**Chart.js 4.4.1** — Client-side charting library loaded from
`cdnjs.cloudflare.com`. No server-side dependency.

**Jinja2 ≥ 3.1** — HTML template rendering for the web UI index page.

**Python Standard Library** — `json`, `random`, `statistics`, `logging`,
`logging.handlers`, `os`, `pathlib`, `dataclasses`, `typing`, `datetime`,
`argparse`, `sys`, `copy`. No other runtime dependencies for the simulation core.

### 6.3 Communication Interfaces

The web interface listens on `127.0.0.1:8000` by default (localhost only).
The `--host 0.0.0.0` flag makes it network-accessible. No authentication
is implemented in the open-source release; network exposure should be managed
at the infrastructure level.

---

## 7. Data Requirements

### 7.1 Organisation JSON Schema

All organisation data is stored and exchanged as JSON conforming to the
following structure (see `examples/rare_earth_org.json` for the canonical reference):

```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "adversarial_org": "boolean (optional, default false)",
  "ao_note": "string (optional — AO inversion explanation for adversarial orgs)",
  "mission_critical_roles": ["role_id_1", "role_id_2"],
  "roles": [
    {
      "id": "string (required — unique snake_case)",
      "title": "string (required)",
      "substitution_timeline": "float [0,4] (required)",
      "documentation_ratio": "float [0,4] (required)",
      "adversarial_observability": "float [0,4] (required)",
      "reports_to": "role_id or null (optional)",
      "critical_dependencies": ["role_id_1"] ,
      "capability_weight": "float >0 (optional, default 1.0)",
      "bench_depth": "integer ≥0 (optional, default 0)",
      "notes": "string (optional)"
    }
  ]
}
```

All role IDs referenced in `mission_critical_roles`, `reports_to`, and
`critical_dependencies` MUST exist in the `roles` array.

### 7.2 Simulation Result Schema

All simulation results are stored in JSON conforming to the SimulationResult
dataclass definition in `kpvs/simulator.py`. The unified summary JSON
written by JSONReporter includes: run_id, timestamp, kpvs_version,
organisation metadata, full kpci_report, all scenario results, cascade results,
and optimiser result.

### 7.3 Output File Organisation

```
<json_dir>/
  <label>_YYYYMMDD_HHMMSS/
    <run_id>_kpci_report.json
    <run_id>_random_attrition.json
    <run_id>_adversarial_targeting_(...).json
    <run_id>_cascade_failure_(...).json  [one per MC role]
    <run_id>_optimizer.json
    <run_id>_summary.json               [unified; used by HTML reporter]

<html_dir>/
  <label>_YYYYMMDD_HHMMSS/
    <run_id>_report.html                [single-org]
    <set_name>_<timestamp>_report.html  [comparative; org-set only]
```

---

## 8. Constraints and Assumptions

### 8.1 Constraints

- KPVS does not collect, infer, or store personally identifiable information.
  All role data is organisational-structural, not individual-biographical.
- The open-source release operates exclusively on publicly available or
  user-supplied data. No classified, proprietary, or controlled data is
  bundled with the distribution.
- The greedy bench optimiser does not guarantee globally optimal allocation.
  It is designed for speed and directional accuracy, not mathematical optimality.

### 8.2 Assumptions

- KPCI component scores are analytical estimates calibrated by the analyst.
  The system assumes input values reflect genuine organisational assessment;
  garbage-in will produce garbage-out without error.
- The capability model assumes all capability is fungible within the weighting
  scheme. Real-world capability interdependencies beyond the explicit dependency
  graph are outside the model's scope.
- The adversarial targeting accuracy parameter (default 0.85) represents the
  probability of optimal target selection on each step. This is consistent with
  documented Thousand Talents targeting precision but is an analytical assumption,
  not an empirically derived value.
- The stochastic cascade failure model uses a Documentation Ratio-weighted
  probability. The specific parameters (0.70 scalar, 0.40 per bench unit) are
  calibrated to produce plausible results consistent with organisational resilience
  literature; they are not derived from empirical incident data.

---

## 9. Acceptance Criteria

The following criteria must be satisfied before any version increment is released:

| Criterion | Standard |
|-----------|----------|
| Test suite | 100% of defined tests pass on Windows, macOS, and Linux |
| Reproducibility | Canonical run (seed=20260501, N=10,000, rare_earth) produces stable adversarial gap within ±0.5 pp across platforms |
| CLI flags | All documented flags accepted without error; `--list-orgs` exits 0 |
| Web interface | All 5 API endpoints return 200 for valid inputs; 422 for invalid org data |
| HTML reports | All reports pass W3C HTML5 validation (no errors); charts render in Chrome, Firefox, Edge |
| Intelligence orgs | All 10 org JSON files load without validation error |
| Air-gap CLI | `python main.py --demo --no-log-file` completes without network access |
| Security | All user-supplied strings HTML-escaped in generated reports; no path traversal via `/reports/` |

---

## 10. Traceability Matrix

| Requirement | Test(s) | Module(s) |
|-------------|---------|-----------|
| FR-001–008 | test_models.py | kpvs/models.py |
| FR-010–020 | test_simulator.py | kpvs/simulator.py |
| FR-030–033 | test_optimizer.py | kpvs/optimizer.py |
| FR-040–047 | test_reporting.py, test_reporting_html.py | kpvs/reporting.py, kpvs/reporting_html.py |
| FR-050–054 | test_reporting_html.py (CLI integration) | main.py |
| FR-060–069 | test_reporting_html.py (webapp integration) | kpvs/webapp/app.py |
| FR-070–073 | test_reporting_html.py (org-set) | kpvs/intelligence/org_loader.py |
| NFR-010 | test_simulator.py::test_seed_reproducibility | kpvs/simulator.py |
| NFR-020–021 | test_reporting_html.py::test_html_escapes_special_chars | kpvs/reporting_html.py |
| NFR-040 | (manual) | main.py, kpvs/ core |

---

*KPVS SRS-001 v1.2.0 — MTS Research Programme — Robert J. Green — May 2026*  
*All KPVS output is analytical and must be calibrated with subject-matter expert review.*
