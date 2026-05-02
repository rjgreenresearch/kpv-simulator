# Changelog

All notable changes to KPVS will be documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] — 2026-05-01

### Added
- Core `Role` and `Organization` data models with full KPCI scoring
- Three Monte Carlo simulation scenarios:
  - `scenario_random_attrition` — baseline natural-turnover model
  - `scenario_adversarial_targeting` — KPCI-weighted preferential targeting
  - `scenario_cascade_failure` — stochastic propagation from mission-critical loss
- `BenchOptimizer` — greedy marginal-improvement bench investment allocator
- `ConsoleReporter` and `JSONReporter` for publication-quality output
- Three built-in example organisations:
  - Rare Earth Processing Programme (MTS Paper 4 / CICP §3.1)
  - Nuclear Stockpile Stewardship Design Team (MTS Paper 5 §4.1)
  - Pharmaceutical KSM Synthesis Facility (MTS Paper 5 §4.4)
- Full CLI (`main.py`) with `--demo`, `--example`, `--org`, `--json-dir`,
  `--iterations`, `--seed`, `--budget`, `--log-level`, `--log-file` flags
- Rotating file log handler (10 MB cap, 5 backups)
- Pytest suite: 80+ tests across models, simulator, optimizer, reporting,
  and logging; all deterministic via fixed seeds
- Apache 2.0 licence, CITATION.cff, README.md, docs/
