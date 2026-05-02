"""
kpvs/reporting.py — Console and JSON Report Formatters
========================================================
Produces publication-quality terminal output and machine-readable
JSON artefacts suitable for embedding in Paper 5 appendices.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Optional

from .models import Organization
from .optimizer import OptimizationResult
from .simulator import KPVSimulator, SimulationResult

logger = logging.getLogger(__name__)

SEP  = "=" * 72
DASH = "─" * 72
VERSION = "1.0.0"


def _tier_badge(tier: str) -> str:
    return {
        "Tier-1 KPV": "[T1]",
        "Tier-2 KPV": "[T2]",
        "Manageable": "[MG]",
        "Resilient":  "[RS]",
    }.get(tier, "[??]")


class ConsoleReporter:
    """Renders a complete KPVS run to stdout."""

    def __init__(self, org: Organization, sim: KPVSimulator) -> None:
        self.org = org
        self.sim = sim

    # ── header ────────────────────────────────────────────────────────────────

    def print_header(self) -> None:
        print(f"\n{SEP}")
        print(f"  KEY PERSON VULNERABILITY SIMULATOR (KPVS) v{VERSION}")
        print(f"  MTS Research Programme — Working Paper 5")
        print(f"  github.com/rjgreenresearch/kpv-simulator")
        print(f"{SEP}")
        print(f"  Organisation : {self.org.name}")
        print(f"  Run ID       : {self.sim.run_id}")
        print(f"  Seed         : {self.sim.seed}")
        print(f"  Timestamp    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Total roles  : {len(self.org.roles)}")
        tier = self.org.tier_summary()
        print(f"  KPCI tiers   : "
              f"{tier['Tier-1 KPV']} Tier-1 | "
              f"{tier['Tier-2 KPV']} Tier-2 | "
              f"{tier['Manageable']} Manageable | "
              f"{tier['Resilient']} Resilient")
        print(SEP)

    # ── KPCI table ───────────────────────────────────────────────────────────

    def print_kpci_table(self) -> None:
        print(f"\n{DASH}")
        print("  KPCI ANALYSIS — ALL ROLES  (sorted by vulnerability)")
        print(DASH)
        header = (f"  {'Role':<38} {'KPCI':>5} {'ST':>4} "
                  f"{'DR':>4} {'AO':>4} {'Bench':>5} {'Restore(mo)':>12}")
        print(header)
        print(f"  {'─'*38} {'─'*5} {'─'*4} {'─'*4} {'─'*4} {'─'*5} {'─'*12}")

        for r in self.org.roles_by_kpci():
            mc = " ★" if r.id in self.org.mission_critical_roles else "  "
            title = (r.title[:35] + "...") if len(r.title) > 35 else r.title
            badge = _tier_badge(r.tier)
            print(
                f"  {badge} {title:<36}{mc} "
                f"{r.kpci:>5.1f} {r.substitution_timeline:>4.1f} "
                f"{r.documentation_ratio:>4.1f} "
                f"{r.adversarial_observability:>4.1f} "
                f"{r.bench_depth:>5} "
                f"{r.estimated_restoration_months:>12.1f}"
            )
        print(f"\n  ★ = Mission-critical role")
        print(f"  [T1]=Tier-1 KPV  [T2]=Tier-2 KPV  "
              f"[MG]=Manageable  [RS]=Resilient")

    # ── Monte Carlo scenario table ────────────────────────────────────────────

    def print_scenario_table(
        self, results: list[SimulationResult], n_losses: int
    ) -> None:
        print(f"\n{DASH}")
        print(f"  MONTE CARLO SCENARIOS  "
              f"(N={results[0].n_iterations:,}  ·  {n_losses} role losses per iteration)")
        print(DASH)
        print(f"  {'Scenario':<44} {'Mean%':>6} {'Median%':>8} "
              f"{'P10%':>6} {'P90%':>6} {'Min%':>6}")
        print(f"  {'─'*44} {'─'*6} {'─'*8} {'─'*6} {'─'*6} {'─'*6}")

        baseline_mean = None
        for result in results:
            label = result.scenario[:43]
            print(
                f"  {label:<44} "
                f"{result.mean_pct:>6.1f} "
                f"{result.median_pct:>8.1f} "
                f"{result.p10_pct:>6.1f} "
                f"{result.p90_pct:>6.1f} "
                f"{result.min_pct:>6.1f}"
            )
            if baseline_mean is None:
                baseline_mean = result.mean_pct

        if len(results) >= 2 and baseline_mean is not None:
            gap = baseline_mean - results[1].mean_pct
            print(f"\n  ► Adversarial targeting gap: {gap:.1f} percentage points "
                  f"below random attrition")
            print(f"    A sophisticated adversary achieves {gap:.1f} pp "
                  f"additional capability loss")
            print(f"    by selecting high-KPCI targets vs. random attrition.")

    # ── Cascade failure block ─────────────────────────────────────────────────

    def print_cascade_results(
        self, cascade_results: list[SimulationResult]
    ) -> None:
        if not cascade_results:
            return
        print(f"\n{DASH}")
        print("  CASCADE FAILURE ANALYSIS — MISSION-CRITICAL ROLES")
        print(DASH)

        for r in cascade_results:
            print(f"\n  Trigger : {r.extra.get('trigger_role_id', '?')}")
            print(f"  Tier    : {r.extra.get('trigger_tier', '?')}  "
                  f"KPCI={r.extra.get('trigger_kpci', '?'):.1f}")
            print(f"  Scenario: {r.scenario}")
            print(f"  Mean residual capability : {r.mean_pct:.1f}%")
            print(f"  Worst-case (P10)         : {r.p10_pct:.1f}%")
            print(f"  Best-case  (P90)         : {r.p90_pct:.1f}%")
            print(f"  Est. restoration         : "
                  f"{r.extra.get('estimated_restoration_months', '?')} months")

    # ── Optimizer block ───────────────────────────────────────────────────────

    def print_optimizer_result(self, opt: OptimizationResult) -> None:
        print(f"\n{DASH}")
        print(f"  OPTIMAL BENCH INVESTMENT — {opt.budget_units}-UNIT ALLOCATION")
        print(f"  (Analogous to CAS simulator optimal portfolio allocation)")
        print(DASH)
        print(f"\n  Baseline capability (adversarial) : "
              f"{opt.baseline_mean_pct:.1f}%")
        print(f"  Optimized capability (adversarial): "
              f"{opt.optimized_mean_pct:.1f}%")
        print(f"  Improvement                       : "
              f"+{opt.improvement_pp:.1f} pp\n")
        print(f"  {'Role':<40} {'KPCI':>5} {'Added':>6} {'Total Bench':>12}")
        print(f"  {'─'*40} {'─'*5} {'─'*6} {'─'*12}")
        for role_id, detail in opt.allocation.items():
            title = detail["title"][:38]
            print(f"  {title:<40} "
                  f"{detail['kpci']:>5.1f} "
                  f"+{detail['units_added']:>5} "
                  f"{detail['total_bench']:>12}")

    # ── Recommendations ───────────────────────────────────────────────────────

    def print_recommendations(self, kpci_report: list[dict]) -> None:
        urgent = [r for r in kpci_report
                  if r["tier"] in ("Tier-1 KPV", "Tier-2 KPV")]
        if not urgent:
            return
        print(f"\n{DASH}")
        print("  PRIORITY RECOMMENDATIONS")
        print(DASH)
        for row in urgent:
            mc = "  ★ MISSION-CRITICAL" if row["mission_critical"] else ""
            print(f"\n  {_tier_badge(row['tier'])} {row['title']}{mc}")
            print(f"  KPCI {row['kpci']:.1f} | "
                  f"Bench: {row['bench_depth']} | "
                  f"Restoration: {row['estimated_restoration_months']} mo | "
                  f"{row['n_dependents']} dependents")
            print(f"  → {row['recommendation']}")

    # ── footer ────────────────────────────────────────────────────────────────

    def print_footer(self) -> None:
        print(f"\n{SEP}")
        print(f"  KPVS v{VERSION}  ·  MTS Paper 5  ·  rjgreenresearch.org")
        print(f"  Cite: Green, R.J. (2026). 'The Irreplaceable Node.'")
        print(f"  All KPCI scores are analytical estimates.")
        print(f"  Calibrate with HR data and subject-matter expert review.")
        print(f"{SEP}\n")


class JSONReporter:
    """Writes machine-readable JSON artefacts to a run directory."""

    def __init__(self, run_dir: str = "runs") -> None:
        self.run_dir = run_dir
        os.makedirs(run_dir, exist_ok=True)
        logger.debug("JSONReporter: output dir '%s'", run_dir)

    def _path(self, filename: str) -> str:
        return os.path.join(self.run_dir, filename)

    def _write(self, filename: str, data: object) -> str:
        path = self._path(filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("JSON written: %s", path)
        return path

    def write_kpci_report(self, report: list[dict], run_id: str) -> str:
        return self._write(f"{run_id}_kpci_report.json", {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "roles": report,
        })

    def write_scenario(self, result: SimulationResult) -> str:
        slug = result.scenario.lower().replace(" ", "_")[:40]
        return self._write(f"{result.run_id}_{slug}.json", result.to_dict())

    def write_optimizer(self, opt: OptimizationResult) -> str:
        return self._write(
            f"{opt.run_id}_optimizer.json", opt.to_dict())

    def write_summary(
        self,
        org: Organization,
        kpci_report: list[dict],
        scenarios: list[SimulationResult],
        cascade_results: list[SimulationResult],
        opt: Optional[OptimizationResult],
        run_id: str,
    ) -> str:
        summary = {
            "run_id":      run_id,
            "timestamp":   datetime.now().isoformat(timespec="seconds"),
            "kpvs_version": VERSION,
            "organisation": {
                "name":        org.name,
                "description": org.description,
                "n_roles":     len(org.roles),
                "tier_summary": org.tier_summary(),
                "total_capability": org.total_capability,
            },
            "kpci_report": kpci_report,
            "scenarios":   [s.to_dict() for s in scenarios],
            "cascade":     [c.to_dict() for c in cascade_results],
            "optimizer":   opt.to_dict() if opt else None,
        }
        return self._write(f"{run_id}_summary.json", summary)
