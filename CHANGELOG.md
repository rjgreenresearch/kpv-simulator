
## [1.1.0] — 2026-05-02

### Added
- `kpvs/reporting_html.py` — self-contained HTML report generator
  - Single-org report with KPCI table, Chart.js distribution charts,
    cascade failure cards, optimizer results, and priority recommendations
  - Multi-org comparative report for `--org-set` runs with gap bar charts
  - Adversarial org AO-inversion banner
  - `--html-dir` CLI flag to specify output directory
  - 15 new pytest tests in `tests/test_reporting_html.py`
- `kpvs/intelligence/` module with `org_loader.py`
  - 10 intelligence org JSON files: us_nsa, uk, ca, au, nz (Five Eyes)
    and cn, ru, ir, kp (adversarial / PASS Act designated)
  - `--intel-org KEY`, `--org-set SET`, `--list-orgs` CLI flags
- `main.py` fix: `--org-set` and `--intel-org` now correctly registered
  with argparse and routed to `run_intel_mode()`

### Fixed
- `--org-set` / `--intel-org` / `--list-orgs` flags were defined but
  not wired into `build_parser()` or `main()` — now fully integrated
- `n_losses=0` treated as falsy in simulator — explicit `None` check
  already in place; confirmed by test suite

## [1.2.0] — 2026-05-02

### Added
- `kpvs/webapp/app.py` — FastAPI web application
  - `GET /` — single-page web UI
  - `GET /api/orgs` — list all available organisations with metadata
  - `GET /api/orgs/{key}` — load a named org (examples + intelligence)
  - `POST /api/run` — execute simulation with user-defined params and org data
  - `GET /api/runs` — run history with links to reports
  - `GET /reports/{path}` — serve generated HTML reports
- `kpvs/webapp/templates/index.html` — full single-page web UI
  - Dark-mode dashboard with sidebar org selector
  - Live org editor: inline-editable KPCI scores, bench depth, role add/delete
  - KPCI recalculates in real-time as values change
  - Mission-critical toggle per role (cascade trigger)
  - Parameters panel: iterations, seed, budget, targeting accuracy slider
  - Results panel: Chart.js charts embedded + full report iframe
  - Run history browser
- `start_webapp.py` — startup script with auto-browser open
  - `python start_webapp.py [--port 8080] [--host 0.0.0.0] [--reload]`
- `main.py` — timestamped output subdirectories
  - `--json-dir runs/` now creates `runs/<label>_YYYYMMDD_HHMMSS/`
  - `--html-dir reports/` now creates `reports/<label>_YYYYMMDD_HHMMSS/`
  - Keeps output paths clean across multiple runs

### Changed
- `requirements.txt` — added fastapi, uvicorn, jinja2, python-multipart, httpx
