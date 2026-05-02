"""
kpvs/webapp/app.py
==================
FastAPI web application for the Key Person Vulnerability Simulator.

Provides a browser-based interface for:
  - Selecting and editing organizational charts
  - Configuring simulation parameters
  - Executing simulations and viewing results
  - Browsing run history

Usage:
  python start_webapp.py               # default: http://localhost:8000
  python start_webapp.py --port 8080   # custom port
"""

from __future__ import annotations

import copy
import json
import logging
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# ── project root on path ─────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from kpvs import Organization, KPVSimulator, BenchOptimizer
from kpvs.examples import (
    build_rare_earth_org,
    build_nuclear_programme_org,
    build_pharma_org,
)
from kpvs.reporting import JSONReporter
from kpvs.reporting_html import HTMLReporter

logger = logging.getLogger("kpvs.webapp")

# ── paths ─────────────────────────────────────────────────────────────────────
WEBAPP_DIR  = Path(__file__).parent
TEMPLATES   = Jinja2Templates(directory=str(WEBAPP_DIR / "templates"))
REPORTS_DIR = ROOT / "reports"
RUNS_DIR    = ROOT / "runs"
REPORTS_DIR.mkdir(exist_ok=True)
RUNS_DIR.mkdir(exist_ok=True)

EXAMPLE_BUILDERS = {
    "rare_earth": build_rare_earth_org,
    "nuclear":    build_nuclear_programme_org,
    "pharma":     build_pharma_org,
}

INTEL_ORG_KEYS = ["us_nsa", "uk", "ca", "au", "nz", "cn", "ru", "ir", "kp"]

# ══════════════════════════════════════════════════════════════════════════════
# Pydantic models
# ══════════════════════════════════════════════════════════════════════════════

class SimParams(BaseModel):
    iterations:          int   = Field(default=10_000, ge=100,    le=100_000)
    seed:                int   = Field(default=20260501)
    n_losses:            Optional[int] = Field(default=None, ge=0)
    budget:              int   = Field(default=3,      ge=0,      le=20)
    targeting_accuracy:  float = Field(default=0.85,   ge=0.01,   le=1.0)
    skip_cascade:        bool  = False
    skip_optimizer:      bool  = False


class RunRequest(BaseModel):
    org_data: dict          # full org JSON (may be user-edited)
    params:   SimParams = SimParams()
    org_key:  Optional[str] = None  # for labelling the run


# ══════════════════════════════════════════════════════════════════════════════
# App
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="KPVS Web Interface",
    description="Key Person Vulnerability Simulator — MTS Research Programme WP-5",
    version="1.1.0",
)

# Serve generated HTML reports at /reports/...
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")


# ══════════════════════════════════════════════════════════════════════════════
# UI route
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return TEMPLATES.TemplateResponse("index.html", {"request": request})


# ══════════════════════════════════════════════════════════════════════════════
# Org API
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/orgs")
async def list_orgs():
    """Return metadata for all available organisations."""
    orgs = []

    # Built-in examples
    for key, builder in EXAMPLE_BUILDERS.items():
        org = builder()
        ts  = org.tier_summary()
        orgs.append({
            "key":      key,
            "group":    "examples",
            "name":     org.name,
            "n_roles":  len(org.roles),
            "t1":       ts["Tier-1 KPV"],
            "t2":       ts["Tier-2 KPV"],
            "mc":       len(org.mission_critical_roles),
        })

    # Intelligence orgs
    for key in INTEL_ORG_KEYS:
        path = _intel_org_path(key)
        if not path or not path.exists():
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            org = Organization.from_dict(data)
            ts  = org.tier_summary()
            orgs.append({
                "key":        key,
                "group":      "adversarial" if data.get("adversarial_org") else "five_eyes",
                "name":       org.name,
                "n_roles":    len(org.roles),
                "t1":         ts["Tier-1 KPV"],
                "t2":         ts["Tier-2 KPV"],
                "mc":         len(org.mission_critical_roles),
                "adversarial": data.get("adversarial_org", False),
            })
        except Exception as e:
            logger.warning("Could not load intel org '%s': %s", key, e)

    return {"orgs": orgs}


@app.get("/api/orgs/{key}")
async def get_org(key: str):
    """Return full JSON for a named org (built-in or intelligence)."""
    if key in EXAMPLE_BUILDERS:
        org  = EXAMPLE_BUILDERS[key]()
        data = org.to_dict()
        data["adversarial_org"] = False
        return data

    path = _intel_org_path(key)
    if path and path.exists():
        with open(path) as f:
            return json.load(f)

    raise HTTPException(status_code=404, detail=f"Org '{key}' not found.")


# ══════════════════════════════════════════════════════════════════════════════
# Simulation API
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/api/run")
async def run_simulation(req: RunRequest):
    """
    Execute a KPVS simulation and return results + report paths.

    The org_data field may contain user-edited KPCI values, bench depths,
    or new roles — the simulation runs against exactly what is submitted.
    """
    run_id    = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    label     = req.org_key or "custom"
    run_folder = f"{label}_{run_id}"

    json_dir  = RUNS_DIR    / run_folder
    html_dir  = REPORTS_DIR / run_folder
    json_dir.mkdir(parents=True, exist_ok=True)
    html_dir.mkdir(parents=True, exist_ok=True)

    # ── Build org ─────────────────────────────────────────────────────────────
    try:
        org = Organization.from_dict(req.org_data)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid org data: {e}")

    adversarial = req.org_data.get("adversarial_org", False)
    p           = req.params

    # ── Simulate ──────────────────────────────────────────────────────────────
    sim = KPVSimulator(org, seed=p.seed, run_id=run_id)

    n_losses = p.n_losses if p.n_losses is not None else max(1, len(org.roles) // 5)

    kpci_report = sim.kpci_report()
    rnd = sim.scenario_random_attrition(n_losses, p.iterations)
    adv = sim.scenario_adversarial_targeting(n_losses, p.iterations,
                                              p.targeting_accuracy)
    adv.extra["adversarial_gap_pp"] = rnd.mean_pct - adv.mean_pct

    cascades = []
    if not p.skip_cascade and org.mission_critical_roles:
        for mc_id in org.mission_critical_roles:
            cascades.append(sim.scenario_cascade_failure(mc_id, p.iterations))

    opt_result = None
    if not p.skip_optimizer and p.budget > 0:
        optimizer = BenchOptimizer(
            org, seed=p.seed,
            eval_iterations=max(200, p.iterations // 20),
        )
        opt_result = optimizer.optimise(p.budget, run_id=run_id)

    # ── Write artefacts ───────────────────────────────────────────────────────
    jr = JSONReporter(str(json_dir))
    jr.write_kpci_report(kpci_report, run_id)
    for s in [rnd, adv]:
        jr.write_scenario(s)
    for c in cascades:
        jr.write_scenario(c)
    if opt_result:
        jr.write_optimizer(opt_result)

    summary_path = jr.write_summary(
        org, kpci_report, [rnd, adv], cascades, opt_result, run_id)

    with open(summary_path) as f:
        summary = json.load(f)
    summary["adversarial_org"] = adversarial
    summary["ao_note"] = req.org_data.get("ao_note", "")

    hr = HTMLReporter(str(html_dir))
    html_path = hr.write_report(summary)
    rel_html  = f"/reports/{run_folder}/{Path(html_path).name}"

    logger.info("Run complete: %s | gap=%.1f pp | report=%s",
                run_id, adv.extra["adversarial_gap_pp"], rel_html)

    return {
        "run_id":       run_id,
        "run_folder":   run_folder,
        "report_url":   rel_html,
        "json_dir":     str(json_dir),
        "summary":      summary,
        "adversarial_gap_pp": adv.extra["adversarial_gap_pp"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# Run history API
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/runs")
async def list_runs(limit: int = 20):
    """List recent simulation runs, most recent first."""
    runs = []
    if not REPORTS_DIR.exists():
        return {"runs": []}

    for entry in sorted(REPORTS_DIR.iterdir(),
                        key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
        if not entry.is_dir():
            continue
        html_files = list(entry.glob("*.html"))
        if not html_files:
            continue
        # Read summary if available
        json_dir = RUNS_DIR / entry.name
        summary_files = list(json_dir.glob("*_summary.json")) if json_dir.exists() else []
        meta = {"run_folder": entry.name, "timestamp": None,
                "org_name": entry.name, "report_url": None}

        if summary_files:
            try:
                with open(summary_files[0]) as f:
                    s = json.load(f)
                meta["org_name"]  = s["organisation"]["name"]
                meta["timestamp"] = s["timestamp"]
                meta["t1"]        = s["organisation"].get("tier_summary", {}).get("Tier-1 KPV", 0)
                meta["gap_pp"]    = next(
                    (sc.get("extra_adversarial_gap_pp") or
                     (s["scenarios"][0]["mean_pct"] - s["scenarios"][1]["mean_pct"])
                     for sc in s.get("scenarios", []) if "Adversarial" in sc.get("scenario","")),
                    None
                )
            except Exception:
                pass

        meta["report_url"] = f"/reports/{entry.name}/{html_files[0].name}"
        runs.append(meta)

    return {"runs": runs}


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _intel_org_path(key: str) -> Optional[Path]:
    """Resolve path for an intelligence org JSON by key."""
    five_eyes = {"uk", "ca", "au", "nz"}
    adversarial = {"cn", "ru", "ir", "kp"}
    name_map = {
        "us_nsa": ROOT / "examples" / "us_national_security_architecture.json",
        "uk":  ROOT / "examples" / "five_eyes" / "uk_national_security.json",
        "ca":  ROOT / "examples" / "five_eyes" / "canada_national_security.json",
        "au":  ROOT / "examples" / "five_eyes" / "australia_national_security.json",
        "nz":  ROOT / "examples" / "five_eyes" / "new_zealand_national_security.json",
        "cn":  ROOT / "examples" / "adversarial" / "china_strategic_leadership.json",
        "ru":  ROOT / "examples" / "adversarial" / "russia_strategic_leadership.json",
        "ir":  ROOT / "examples" / "adversarial" / "iran_strategic_leadership.json",
        "kp":  ROOT / "examples" / "adversarial" / "north_korea_strategic_leadership.json",
    }
    return name_map.get(key)
